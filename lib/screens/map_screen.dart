import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

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
      final response = await http.get(Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/search'));

      if (response.statusCode == 200) {
        final List<dynamic> ridesData = json.decode(response.body);
        Set<Marker> newMarkers = Set.from(_markers); // Keep existing markers (like user's location)
        Set<Polyline> newPolylines = {};

        for (var ride in ridesData) {
          final String fromLocation = ride['from_location'];
          final String toLocation = ride['to_location'];
          final String driverName = ride['driver_name'] ?? 'Neznámý řidič';
          final List<dynamic> routeWaypoints = ride['route_waypoints'] ?? [];

          // Create LatLng points from waypoints
          List<LatLng> points = [];
          if (routeWaypoints.isNotEmpty) {
            for (var waypoint in routeWaypoints) {
              if (waypoint is Map<String, dynamic> &&
                  waypoint.containsKey('lat') &&
                  waypoint.containsKey('lng')) {
                points.add(LatLng(waypoint['lat'], waypoint['lng']));
              }
            }
          }

          // Add markers for start and end points of the ride
          if (points.isNotEmpty) {
            newMarkers.add(
              Marker(
                markerId: MarkerId('ride_start_${ride['id']}'),
                position: points.first,
                infoWindow: InfoWindow(
                  title: '$driverName: $fromLocation',
                  snippet: 'Odjezd: ${ride['departure_time']}',
                  onTap: () => _showRideInfo(ride),
                ),
                icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
              ),
            );
            newMarkers.add(
              Marker(
                markerId: MarkerId('ride_end_${ride['id']}'),
                position: points.last,
                infoWindow: InfoWindow(
                  title: '$driverName: $toLocation',
                  snippet: 'Příjezd: ${ride['departure_time']}', // Assuming departure time is relevant for end too
                  onTap: () => _showRideInfo(ride),
                ),
                icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
              ),
            );

            // Add polyline for the route
            newPolylines.add(
              Polyline(
                polylineId: PolylineId('ride_route_${ride['id']}'),
                points: points,
                color: Colors.blue,
                width: 5,
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
                target: _currentPosition,
                zoom: 13.0,
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