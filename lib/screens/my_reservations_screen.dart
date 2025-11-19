import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

import '../config/api_config.dart';

class MyReservationsScreen extends StatefulWidget {
  const MyReservationsScreen({super.key});

  @override
  State<MyReservationsScreen> createState() => _MyReservationsScreenState();
}

class _MyReservationsScreenState extends State<MyReservationsScreen> {
  List<dynamic> _reservations = [];
  bool _isLoading = true;
  String? _error;
  Widget _addressRow(String label, String? value, IconData icon) {
    final display =
        (value ?? '').trim().isEmpty ? 'Neznámá adresa' : value!.trim();
    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Colors.grey.shade600),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              '$label: $display',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _fetchReservations();
  }

  Future<void> _cancelReservation(int reservationId) async {
    try {
      // Simulace zrušení rezervace
      setState(() {
        _reservations.removeWhere((r) => r['id'] == reservationId);
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Rezervace byla zrušena'),
          backgroundColor: Colors.orange,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba při rušení: $e')),
      );
    }
  }

  Future<void> _fetchReservations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id') ?? 1;
      
      final response = await http.get(
        ApiConfig.uri('/api/reservations', query: {'user_id': userId}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _reservations = data;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nepodařilo se načíst rezervace. Kód: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Chyba připojení: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rezervované jízdy'),
        backgroundColor: Colors.amber,
        foregroundColor: Colors.white,
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _isLoading = true;
                  _error = null;
                });
                _fetchReservations();
              },
              child: const Text('Zkusit znovu'),
            ),
          ],
        ),
      );
    }

    if (_reservations.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_seat_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Nemáte rezervované žádné jízdy.'),
            SizedBox(height: 8),
            Text('Vyhledejte jízdu a rezervujte si místo!', 
                 style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchReservations,
      child: ListView.builder(
        padding: const EdgeInsets.all(8.0),
        itemCount: _reservations.length,
        itemBuilder: (context, index) {
          final reservation = _reservations[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.amber,
                child: Text(
                  '${reservation['seats_reserved']}',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text(
                '${reservation['from_location'] ?? 'Neznámé'} → ${reservation['to_location'] ?? 'Neznámé'}',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  _addressRow('Odkud', reservation['from_location'],
                      Icons.location_on_outlined),
                  _addressRow('Kam', reservation['to_location'],
                      Icons.flag_outlined),
                  const SizedBox(height: 2),
                  Text('Řidič: ${reservation['driver_name'] ?? 'Neznámý'}'),
                  Text('Čas: ${reservation['departure_time'] ?? 'Neznámý'}'),
                  Row(
                    children: [
                      const Icon(Icons.event_seat, size: 16, color: Colors.amber),
                      const SizedBox(width: 4),
                      Text('${reservation['seats_reserved']} místo'),
                      const SizedBox(width: 16),
                      const Icon(Icons.attach_money, size: 16, color: Colors.green),
                      const SizedBox(width: 4),
                      Text('${reservation['price_per_person'] ?? 0} Kč'),
                    ],
                  ),
                  Row(
                    children: [
                      const Icon(Icons.check_circle, size: 16, color: Colors.green),
                      const SizedBox(width: 4),
                      Text('Status: ${reservation['status']}'),
                    ],
                  ),
                ],
              ),
              trailing: SizedBox(
                width: 150,
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    SizedBox(
                      width: 140,
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.pushNamed(context, '/chat', arguments: {
                            'contact_name':
                                reservation['driver_name'] ?? 'Neznámý řidič',
                            'contact_phone':
                                reservation['driver_phone'] ?? '+420721745084',
                            'ride_info':
                                '${reservation['from_location']} → ${reservation['to_location']}'
                          });
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Chat'),
                      ),
                    ),
                    SizedBox(
                      width: 140,
                      child: ElevatedButton(
                        onPressed: () => _cancelReservation(reservation['id']),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Zrušit'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
