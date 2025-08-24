import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class DriverReservationsScreen extends StatefulWidget {
  const DriverReservationsScreen({super.key});

  @override
  State<DriverReservationsScreen> createState() => _DriverReservationsScreenState();
}

class _DriverReservationsScreenState extends State<DriverReservationsScreen> {
  List<dynamic> _reservations = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchReservations();
  }

  Future<void> _fetchReservations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final driverId = prefs.getInt('user_id');
      
      final response = await http.get(
        Uri.parse('http://localhost:8081/api/reservations/driver/$driverId'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _reservations = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Moji pasažéři')),
      body: _isLoading
        ? const Center(child: CircularProgressIndicator())
        : _reservations.isEmpty
          ? const Center(child: Text('Žádní pasažéři'))
          : ListView.builder(
              itemCount: _reservations.length,
              itemBuilder: (context, index) {
                final reservation = _reservations[index];
                return Card(
                  margin: const EdgeInsets.all(8.0),
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.person)),
                    title: Text(reservation['passenger_name']),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${reservation['from_location']} → ${reservation['to_location']}'),
                        Text('Čas: ${reservation['departure_time']}'),
                        Text('Míst: ${reservation['seats_reserved']}'),
                      ],
                    ),
                    trailing: ElevatedButton(
                      onPressed: () {
                        Navigator.pushNamed(
                          context,
                          '/rating',
                          arguments: {
                            'ride_id': reservation['ride_id'],
                            'rated_user_id': reservation['passenger_id'],
                            'rated_user_name': reservation['passenger_name'],
                          },
                        );
                      },
                      child: const Text('Hodnotit'),
                    ),
                  ),
                );
              },
            ),
    );
  }
}