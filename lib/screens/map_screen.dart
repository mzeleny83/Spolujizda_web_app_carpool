import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../config/api_config.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  GoogleMapController? mapController;
  LatLng _currentPosition = const LatLng(49.1951, 16.6068); // Brno
  Set<Marker> _markers = {};
  Set<Polyline> _polylines = {}; // Added for drawing routes
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
    _getCurrentLocation();
    _loadRides(); // Changed from _loadDrivers to _loadRides
  }

  Future<void> _getCurrentLocation() async {
    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.whileInUse || 
          permission == LocationPermission.always) {
        Position position = await Geolocator.getCurrentPosition();
        setState(() {
          _currentPosition = LatLng(position.latitude, position.longitude);
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadRides() async {
    setState(() {
      _isLoading = true;
      _markers.clear();
      _polylines.clear();
    });

    // Add user's current location marker
    _markers.add(
      Marker(
        markerId: const MarkerId('my_location'),
        position: _currentPosition,
        infoWindow: const InfoWindow(title: 'Moje poloha'),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
      ),
    );

    try {
      final response = await http.get(ApiConfig.uri('/api/rides/search'));

      if (response.statusCode == 200) {
        final List<dynamic> ridesData = json.decode(response.body);
        Set<Marker> newMarkers = Set.from(_markers); // Keep existing markers (like user's location)
        Set<Polyline> newPolylines = {};

        for (var ride in ridesData) {
          final String fromLocation = ride['from_location'];
          final String toLocation = ride['to_location'];
          final String driverName = ride['driver_name'] ?? 'Neznámý řidič';
          
          // Get real coordinates for cities
          final LatLng? startCoords = _cityCoordinates[fromLocation];
          final LatLng? endCoords = _cityCoordinates[toLocation];
          
          if (startCoords != null && endCoords != null) {
            // Add start marker
            newMarkers.add(
              Marker(
                markerId: MarkerId('ride_start_${ride['id']}'),
                position: startCoords,
                infoWindow: InfoWindow(
                  title: '$driverName: $fromLocation',
                  snippet: 'Odjezd: ${ride['departure_time']}\nCena: ${ride['price_per_person']} Kč',
                  onTap: () => _showRideInfo(ride),
                ),
                icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
              ),
            );
            
            // Add end marker
            newMarkers.add(
              Marker(
                markerId: MarkerId('ride_end_${ride['id']}'),
                position: endCoords,
                infoWindow: InfoWindow(
                  title: '$driverName: $toLocation',
                  snippet: 'Volná místa: ${ride['available_seats']}',
                  onTap: () => _showRideInfo(ride),
                ),
                icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
              ),
            );

            // Add simple route line
            newPolylines.add(
              Polyline(
                polylineId: PolylineId('ride_route_${ride['id']}'),
                points: [startCoords, endCoords],
                color: _getRouteColor(ride['id']),
                width: 4,
                patterns: [PatternItem.dash(20), PatternItem.gap(10)],
              ),
            );
          }
        }

        setState(() {
          _markers = newMarkers;
          _polylines = newPolylines;
          _isLoading = false;
        });
      } else {
        // Handle server error
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Chyba při načítání jízd: ${response.statusCode}')),
        );
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba sítě při načítání jízd: $e')),
      );
    }
  }

  Color _getRouteColor(int rideId) {
    final colors = [Colors.blue, Colors.red, Colors.green, Colors.orange, Colors.purple, Colors.teal];
    return colors[rideId % colors.length];
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
                    // Navigate to chat screen, potentially passing ride_id or driver_id
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
                    // Implement actual reservation logic here
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
        title: const Text('Mapa jízd'), // Changed title
        actions: [
          IconButton(
            icon: const Icon(Icons.my_location),
            onPressed: () {
              mapController?.animateCamera(
                CameraUpdate.newLatLng(_currentPosition),
              );
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : GoogleMap(
              onMapCreated: (GoogleMapController controller) {
                mapController = controller;
              },
              initialCameraPosition: CameraPosition(
                target: const LatLng(49.75, 15.5), // Center of Czech Republic
                zoom: 7.0, // Zoom out to see whole country
              ),
              markers: _markers,
              polylines: _polylines, // Added polylines
              myLocationEnabled: true,
              myLocationButtonEnabled: false,
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/find'),
        child: const Icon(Icons.search),
      ),
    );
  }
}
