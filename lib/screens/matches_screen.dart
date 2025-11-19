import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

import '../config/api_config.dart';

class MatchesScreen extends StatefulWidget {
  const MatchesScreen({super.key});

  @override
  State<MatchesScreen> createState() => _MatchesScreenState();
}

class _MatchesScreenState extends State<MatchesScreen> {
  List<dynamic> _rides = [];
  bool _isLoading = true;
  String? _error;
  Set<int> _reservedRides = {};

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
  void didChangeDependencies() {
    super.didChangeDependencies();
    _fetchRides();
  }

  Future<void> _fetchRides() async {
    try {
      final arguments = ModalRoute.of(context)!.settings.arguments as Map<String, String?>?;
      final from = arguments?['from'] ?? '';
      final to = arguments?['to'] ?? '';
      
      final query = <String, String>{};
      if (from.isNotEmpty) {
        query['from'] = from;
      }
      if (to.isNotEmpty) {
        query['to'] = to;
      }
      
      final response = await http.get(
        ApiConfig.uri('/api/rides/search', query: query.isEmpty ? null : query),
      );

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
            _rides = data;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to load rides. Status code: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'An error occurred: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nalezené jízdy')),
      body: _buildBody(),
    );
  }

  Future<void> _reserveRide(int rideId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id') ?? 1;
      
      final response = await http.post(
        ApiConfig.uri('/api/rides/reserve'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ride_id': rideId,
          'passenger_id': userId,
          'seats_reserved': 1,
        }),
      );
      
      if (response.statusCode == 201) {
        setState(() {
          _reservedRides.add(rideId);
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✓ Jízda byla úspěšně zarezervována!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        final data = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(data['error'] ?? 'Chyba při rezervaci')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba připojení: $e')),
      );
    }
  }

  Widget _buildRatingStars(double rating) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (index) {
        return Icon(
          index < rating.floor() ? Icons.star : 
          index < rating ? Icons.star_half : Icons.star_border,
          color: Colors.amber,
          size: 20,
        );
      }),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!));
    }

    if (_rides.isEmpty) {
      return const Center(child: Text('Nebyly nalezeny žádné jízdy.'));
    }

    return ListView.builder(
      itemCount: _rides.length,
      itemBuilder: (context, index) {
        final ride = _rides[index];
        return Card(
          margin: const EdgeInsets.all(8.0),
          child: ListTile(
            leading: const CircleAvatar(
              child: Icon(Icons.person),
            ),
            title: Text(ride['driver_name'] ?? 'Neznámý řidič'),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildRatingStars(ride['driver_rating']?.toDouble() ?? 5.0),
                const SizedBox(height: 4),
                _addressRow('Odkud', ride['from_location'],
                    Icons.location_on_outlined),
                _addressRow('Kam', ride['to_location'], Icons.flag_outlined),
                const SizedBox(height: 2),
                Text('Čas: ${ride['departure_time']}'),
                Text('Cena: ${ride['price_per_person']} Kč '
                    '| Volná místa: ${ride['available_seats']}'),
              ],
            ),
            trailing: SizedBox(
              width: 150,
              child: _reservedRides.contains(ride['id'])
                  ? const Chip(
                      label: Text('Rezervováno'),
                      backgroundColor: Colors.green,
                      labelStyle: TextStyle(color: Colors.white),
                    )
                  : Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        SizedBox(
                          width: 140,
                          child: ElevatedButton(
                            onPressed: () => _reserveRide(ride['id']),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue,
                              foregroundColor: Colors.white,
                            ),
                            child: const Text('Rezervovat'),
                          ),
                        ),
                        SizedBox(
                          width: 140,
                          child: ElevatedButton(
                            onPressed: () {
                              Navigator.pushNamed(context, '/chat', arguments: {
                                'contact_name': ride['driver_name'],
                                'contact_phone':
                                    ride['driver_phone'] ?? '+420721745084',
                                'ride_info':
                                    '${ride['from_location']} → ${ride['to_location']}'
                              });
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.green,
                              foregroundColor: Colors.white,
                            ),
                            child: const Text('Chat'),
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        );
      },
    );
  }
}
