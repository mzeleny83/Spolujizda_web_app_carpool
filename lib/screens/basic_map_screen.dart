import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../config/api_config.dart';

class BasicMapScreen extends StatefulWidget {
  const BasicMapScreen({super.key});

  @override
  State<BasicMapScreen> createState() => _BasicMapScreenState();
}

class _BasicMapScreenState extends State<BasicMapScreen> {
  List<dynamic> _rides = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRides();
  }

  Future<void> _loadRides() async {
    try {
      final response = await http.get(ApiConfig.uri('/api/rides/search'));

      if (response.statusCode == 200) {
        final List<dynamic> ridesData = json.decode(response.body);
        setState(() {
          _rides = ridesData;
          _isLoading = false;
        });
      } else {
        setState(() => _isLoading = false);
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mapa jízd'),
        backgroundColor: Colors.blue,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Vizuální mapa
                Container(
                  height: 250,
                  width: double.infinity,
                  margin: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.green[100],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.green, width: 2),
                  ),
                  child: Stack(
                    children: [
                      // Pozadí mapy
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(10),
                          gradient: LinearGradient(
                            colors: [Colors.green[50]!, Colors.blue[50]!],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                        ),
                      ),
                      // Města na mapě
                      const Positioned(
                        top: 50,
                        left: 80,
                        child: _CityMarker(name: 'Praha', color: Colors.red),
                      ),
                      const Positioned(
                        bottom: 80,
                        left: 120,
                        child: _CityMarker(name: 'Brno', color: Colors.blue),
                      ),
                      const Positioned(
                        top: 70,
                        right: 60,
                        child: _CityMarker(name: 'Ostrava', color: Colors.green),
                      ),
                      // Trasy
                      CustomPaint(
                        size: Size.infinite,
                        painter: RoutesPainter(),
                      ),
                    ],
                  ),
                ),
                // Seznam jízd
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _rides.length,
                    itemBuilder: (context, index) {
                      final ride = _rides[index];
                      return Card(
                        elevation: 3,
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getCityColor(ride['from_location']),
                            child: const Icon(Icons.directions_car, color: Colors.white),
                          ),
                          title: Text(
                            '${ride['from_location']} → ${ride['to_location']}',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Řidič: ${ride['driver_name']}'),
                              Text('Čas: ${ride['departure_time']}'),
                              Text('${ride['price_per_person']} Kč • ${ride['available_seats']} míst'),
                            ],
                          ),
                          trailing: ElevatedButton(
                            onPressed: () => Navigator.pushNamed(context, '/chat'),
                            child: const Text('Kontakt'),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Color _getCityColor(String city) {
    switch (city) {
      case 'Praha': return Colors.red;
      case 'Brno': return Colors.blue;
      case 'Ostrava': return Colors.green;
      default: return Colors.grey;
    }
  }
}

class _CityMarker extends StatelessWidget {
  final String name;
  final Color color;

  const _CityMarker({required this.name, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            name,
            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
          ),
        ),
        Icon(Icons.location_on, color: color, size: 24),
      ],
    );
  }
}

class RoutesPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue.withOpacity(0.6)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    // Praha -> Brno
    canvas.drawLine(
      Offset(size.width * 0.3, size.height * 0.3),
      Offset(size.width * 0.5, size.height * 0.7),
      paint,
    );

    // Brno -> Ostrava
    paint.color = Colors.green.withOpacity(0.6);
    canvas.drawLine(
      Offset(size.width * 0.5, size.height * 0.7),
      Offset(size.width * 0.8, size.height * 0.4),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
