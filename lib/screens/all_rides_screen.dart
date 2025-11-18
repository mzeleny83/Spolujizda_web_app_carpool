import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class AllRidesScreen extends StatefulWidget {
  const AllRidesScreen({super.key});

  @override
  State<AllRidesScreen> createState() => _AllRidesScreenState();
}

class _AllRidesScreenState extends State<AllRidesScreen> {
  List<dynamic> _rides = [];
  bool _isLoading = true;
  String? _error;
  Set<int> _reservedRides = {};

  @override
  void initState() {
    super.initState();
    _fetchAllRides();
  }

  Future<void> _fetchAllRides() async {
    try {
      final response = await http.get(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/search'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _rides = data;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nepodařilo se načíst jízdy. Kód: ${response.statusCode}';
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

  Future<void> _reserveRide(int rideId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id') ?? 1;
      
      final response = await http.post(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/reserve'),
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
          size: 16,
        );
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Všechny dostupné jízdy'),
        backgroundColor: Colors.teal,
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
                _fetchAllRides();
              },
              child: const Text('Zkusit znovu'),
            ),
          ],
        ),
      );
    }

    if (_rides.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.directions_car_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Momentálně nejsou k dispozici žádné jízdy.'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchAllRides,
      child: ListView.builder(
        padding: const EdgeInsets.all(8.0),
        itemCount: _rides.length,
        itemBuilder: (context, index) {
          final ride = _rides[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.teal,
                child: Text(
                  (ride['driver_name'] ?? 'N')[0].toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text(
                ride['driver_name'] ?? 'Neznámý řidič',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  _buildRatingStars(ride['driver_rating']?.toDouble() ?? 5.0),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.location_on, size: 16, color: Colors.green),
                      const SizedBox(width: 4),
                      Expanded(child: Text(ride['from_location'] ?? '')),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      const Icon(Icons.flag, size: 16, color: Colors.red),
                      const SizedBox(width: 4),
                      Expanded(child: Text(ride['to_location'] ?? '')),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.access_time, size: 16, color: Colors.blue),
                      const SizedBox(width: 4),
                      Text(ride['departure_time'] ?? ''),
                      const Spacer(),
                      const Icon(Icons.attach_money, size: 16, color: Colors.orange),
                      Text('${ride['price_per_person']} Kč'),
                    ],
                  ),
                ],
              ),
              trailing: _reservedRides.contains(ride['id'])
                  ? const Chip(
                      label: Text('Rezervováno'),
                      backgroundColor: Colors.green,
                      labelStyle: TextStyle(color: Colors.white),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        ElevatedButton(
                          onPressed: () => _reserveRide(ride['id']),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.teal,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                          ),
                          child: const Text('Rezervovat'),
                        ),
                        const SizedBox(width: 4),
                        ElevatedButton(
                          onPressed: () {
                            Navigator.pushNamed(context, '/chat', arguments: {
                              'contact_name': ride['driver_name'],
                              'contact_phone': '+420721745084',
                              'ride_info': '${ride['from_location']} → ${ride['to_location']}'
                            });
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                          ),
                          child: const Text('Chat'),
                        ),
                      ],
                    ),
            ),
          );
        },
      ),
    );
  }
}