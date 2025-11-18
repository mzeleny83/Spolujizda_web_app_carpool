import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class OSMMapScreen extends StatefulWidget {
  const OSMMapScreen({super.key});

  @override
  State<OSMMapScreen> createState() => _OSMMapScreenState();
}

class _OSMMapScreenState extends State<OSMMapScreen> {
  final MapController _mapController = MapController();
  List<Marker> _markers = [];
  List<Polyline> _polylines = [];
  bool _isLoading = true;

  // Real GPS coordinates for Czech cities
  final Map<String, LatLng> _cityCoordinates = {
    'Praha': const LatLng(50.0755, 14.4378),
    'Brno': const LatLng(49.1951, 16.6068),
    'Ostrava': const LatLng(49.8209, 18.2625),
    'Plzeň': const LatLng(49.7384, 13.3736),
    'České Budějovice': const LatLng(48.9745, 14.4743),
    'Liberec': const LatLng(50.7663, 15.0543),
  };

  @override
  void initState() {
    super.initState();
    _loadRides();
  }

  Future<void> _loadRides() async {
    setState(() {
      _isLoading = true;
      _markers.clear();
      _polylines.clear();
    });

    try {
      final response = await http.get(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/search')
      );

      if (response.statusCode == 200) {
        final List<dynamic> ridesData = json.decode(response.body);
        List<Marker> newMarkers = [];
        List<Polyline> newPolylines = [];

        for (var ride in ridesData) {
          final String fromLocation = ride['from_location'];
          final String toLocation = ride['to_location'];
          final String driverName = ride['driver_name'] ?? 'Neznámý řidič';
          
          final LatLng? startCoords = _cityCoordinates[fromLocation];
          final LatLng? endCoords = _cityCoordinates[toLocation];
          
          if (startCoords != null && endCoords != null) {
            // Add start marker
            newMarkers.add(
              Marker(
                point: startCoords,
                width: 40,
                height: 40,
                child: GestureDetector(
                  onTap: () => _showRideInfo(ride),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.green,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: const Icon(Icons.directions_car, color: Colors.white, size: 20),
                  ),
                ),
              ),
            );
            
            // Add end marker
            newMarkers.add(
              Marker(
                point: endCoords,
                width: 40,
                height: 40,
                child: GestureDetector(
                  onTap: () => _showRideInfo(ride),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: const Icon(Icons.location_on, color: Colors.white, size: 20),
                  ),
                ),
              ),
            );

            // Add route line
            newPolylines.add(
              Polyline(
                points: [startCoords, endCoords],
                color: _getRouteColor(ride['id']),
                strokeWidth: 3.0,
                isDotted: true,
              ),
            );
          }
        }

        setState(() {
          _markers = newMarkers;
          _polylines = newPolylines;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba načítání jízd: $e')),
      );
    }
  }

  Color _getRouteColor(int rideId) {
    final colors = [Colors.blue, Colors.red, Colors.green, Colors.orange, Colors.purple, Colors.teal];
    return colors[rideId % colors.length];
  }

  void _showAllRides() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.3,
        builder: (context, scrollController) => Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const Text(
                'Všechny dostupné jízdy',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: FutureBuilder<List<dynamic>>(
                  future: _fetchAllRides(),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError) {
                      return Center(child: Text('Chyba: ${snapshot.error}'));
                    }
                    final rides = snapshot.data ?? [];
                    return ListView.builder(
                      controller: scrollController,
                      itemCount: rides.length,
                      itemBuilder: (context, index) {
                        final ride = rides[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: _getRouteColor(ride['id']),
                              child: const Icon(Icons.directions_car, color: Colors.white),
                            ),
                            title: Text('${ride['from_location']} → ${ride['to_location']}'),
                            subtitle: Text(
                              'Řidič: ${ride['driver_name']}\n'
                              'Čas: ${ride['departure_time']}\n'
                              'Cena: ${ride['price_per_person']} Kč | Místa: ${ride['available_seats']}'
                            ),
                            isThreeLine: true,
                            onTap: () {
                              Navigator.pop(context);
                              _showRideInfo(ride);
                              // Zoom to route on map
                              final startCoords = _cityCoordinates[ride['from_location']];
                              final endCoords = _cityCoordinates[ride['to_location']];
                              if (startCoords != null && endCoords != null) {
                                _mapController.fitCamera(
                                  CameraFit.bounds(
                                    bounds: LatLngBounds(startCoords, endCoords),
                                    padding: const EdgeInsets.all(50),
                                  ),
                                );
                              }
                            },
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<List<dynamic>> _fetchAllRides() async {
    try {
      final response = await http.get(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/search')
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      // Handle error
    }
    return [];
  }

  void _showRideInfo(Map<String, dynamic> ride) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Jízda s ${ride['driver_name'] ?? 'Neznámý řidič'}',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text('Trasa: ${ride['from_location']} → ${ride['to_location']}'),
            Text('Čas odjezdu: ${ride['departure_time']}'),
            Text('Volná místa: ${ride['available_seats']}'),
            Text('Cena: ${ride['price_per_person']} Kč'),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    Navigator.pushNamed(context, '/chat');
                  },
                  child: const Text('Kontaktovat'),
                ),
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Žádost o jízdu odeslána!')),
                    );
                  },
                  child: const Text('Rezervovat'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mapa jízd (OpenStreetMap)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: _showAllRides,
            tooltip: 'Všechny jízdy',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRides,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : FlutterMap(
              mapController: _mapController,
              options: const MapOptions(
                initialCenter: LatLng(49.75, 15.5), // Center of Czech Republic
                initialZoom: 7.0,
                minZoom: 6.0,
                maxZoom: 18.0,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.spolujizda',
                  maxNativeZoom: 19,
                ),
                PolylineLayer(polylines: _polylines),
                MarkerLayer(markers: _markers),
              ],
            ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            heroTag: "rides_list",
            onPressed: _showAllRides,
            backgroundColor: Colors.green,
            child: const Icon(Icons.list),
          ),
          const SizedBox(height: 10),
          FloatingActionButton(
            heroTag: "search",
            onPressed: () => Navigator.pushNamed(context, '/find'),
            child: const Icon(Icons.search),
          ),
        ],
      ),
    );
  }
}