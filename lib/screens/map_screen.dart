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

  // Mapping of accented characters to ASCII (using char codes to avoid encoding issues)
  static const Map<int, String> _accentReplacements = {
    0x00E1: 'a',
    0x00E0: 'a',
    0x00E4: 'a',
    0x010D: 'c',
    0x00E7: 'c',
    0x010F: 'd',
    0x00E9: 'e',
    0x011B: 'e',
    0x00ED: 'i',
    0x00EF: 'i',
    0x013A: 'l',
    0x0142: 'l',
    0x0148: 'n',
    0x00F3: 'o',
    0x00F4: 'o',
    0x00F6: 'o',
    0x0159: 'r',
    0x0161: 's',
    0x0165: 't',
    0x00FA: 'u',
    0x016F: 'u',
    0x00FC: 'u',
    0x00FD: 'y',
    0x017E: 'z',
  };

  // Real GPS coordinates for Czech cities (stored with normalized ASCII keys)
  final Map<String, LatLng> _cityCoordinates = {
    'praha': const LatLng(50.0755, 14.4378),
    'brno': const LatLng(49.1951, 16.6068),
    'ostrava': const LatLng(49.8209, 18.2625),
    'plzen': const LatLng(49.7384, 13.3736),
    'ceske budejovice': const LatLng(48.9745, 14.4743),
    'liberec': const LatLng(50.7663, 15.0543),
    'olomouc': const LatLng(49.5938, 17.2509),
    'hradec kralove': const LatLng(50.2092, 15.8328),
    'pardubice': const LatLng(50.0343, 15.7812),
    'usti nad labem': const LatLng(50.66, 14.04),
    'zlin': const LatLng(49.2264, 17.6676),
    'jihlava': const LatLng(49.396, 15.5912),
    'karvina': const LatLng(49.8567, 18.5417),
    'opava': const LatLng(49.9387, 17.9039),
    'karlovy vary': const LatLng(50.2319, 12.871),
    'kladno': const LatLng(50.1475, 14.1028),
    'most': const LatLng(50.503, 13.636),
    'teplice': const LatLng(50.64, 13.826),
    'chomutov': const LatLng(50.46, 13.4178),
    'trinec': const LatLng(49.6778, 18.6708),
    'znojmo': const LatLng(48.8555, 16.0488),
    'havirov': const LatLng(49.78, 18.4363),
    'prostejov': const LatLng(49.4719, 17.1118),
    'prerov': const LatLng(49.4556, 17.45),
    'tabor': const LatLng(49.4144, 14.6578),
    'trutnov': const LatLng(50.561, 15.9127),
    'sumperk': const LatLng(49.9653, 16.9706),
    'uherske hradiste': const LatLng(49.0698, 17.4597),
  };

  String _normalizeLocation(String value) {
    final lower = value.toLowerCase();
    final buffer = StringBuffer();
    for (final codeUnit in lower.codeUnits) {
      buffer.write(
          _accentReplacements[codeUnit] ?? String.fromCharCode(codeUnit));
    }
    final cleaned =
        buffer.toString().replaceAll(RegExp(r'[^a-z0-9 ]'), ' ').trim();
    return cleaned.replaceAll(RegExp(r'\s+'), ' ');
  }

  LatLng? _resolveCoordinates(String location) {
    final normalized = _normalizeLocation(location);
    if (normalized.isEmpty) return null;

    if (_cityCoordinates.containsKey(normalized)) {
      return _cityCoordinates[normalized];
    }

    for (final entry in _cityCoordinates.entries) {
      if (normalized.contains(entry.key) || entry.key.contains(normalized)) {
        return entry.value;
      }
    }

    for (final token in normalized.split(' ').reversed) {
      final coord = _cityCoordinates[token];
      if (coord != null) return coord;
    }
    return null;
  }

  LatLng? _extractCoordinates(
    Map<String, dynamic> ride,
    String latKey,
    String lngKey,
    String fallbackLocation,
  ) {
    final latValue = ride[latKey];
    final lngValue = ride[lngKey];

    if (latValue != null && lngValue != null) {
      final lat = double.tryParse(latValue.toString());
      final lng = double.tryParse(lngValue.toString());
      if (lat != null && lng != null) {
        return LatLng(lat, lng);
      }
    }

    return _resolveCoordinates(fallbackLocation);
  }

  List<LatLng> _buildRoutePoints(
    LatLng start,
    LatLng end,
    dynamic rawWaypoints,
  ) {
    final points = <LatLng>[start];
    final decoded = _decodeWaypoints(rawWaypoints);
    if (decoded != null && decoded.isNotEmpty) {
      points.addAll(decoded);
    }
    points.add(end);
    return points;
  }

  List<LatLng>? _decodeWaypoints(dynamic rawWaypoints) {
    if (rawWaypoints == null) return null;
    try {
      dynamic data = rawWaypoints;
      if (rawWaypoints is String && rawWaypoints.trim().isNotEmpty) {
        data = jsonDecode(rawWaypoints);
      }

      if (data is List) {
        return data
            .map<LatLng?>((point) {
              if (point is Map) {
                final lat = point['lat'] ?? point['latitude'];
                final lng = point['lng'] ?? point['longitude'];
                if (lat != null && lng != null) {
                  final latDouble = double.tryParse(lat.toString());
                  final lngDouble = double.tryParse(lng.toString());
                  if (latDouble != null && lngDouble != null) {
                    return LatLng(latDouble, lngDouble);
                  }
                }
              }
              return null;
            })
            .whereType<LatLng>()
            .toList();
      }
    } catch (_) {
      // Ignore decoding errors and fall back to start -> end polyline
    }
    return null;
  }

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
        Set<Marker> newMarkers =
            Set.from(_markers); // Keep existing markers (like user's location)
        Set<Polyline> newPolylines = {};

        for (var ride in ridesData) {
          final String fromLocation = (ride['from_location'] ?? '').toString();
          final String toLocation = (ride['to_location'] ?? '').toString();
          final String driverName =
              (ride['driver_name'] ?? 'Neznámý řidič').toString();

          final LatLng? startCoords = _extractCoordinates(
            ride,
            'from_lat',
            'from_lng',
            fromLocation,
          );
          final LatLng? endCoords = _extractCoordinates(
            ride,
            'to_lat',
            'to_lng',
            toLocation,
          );

          if (startCoords != null && endCoords != null) {
            // Add start marker
            newMarkers.add(
              Marker(
                markerId: MarkerId('ride_start_${ride['id']}'),
                position: startCoords,
                infoWindow: InfoWindow(
                  title: '$driverName: $fromLocation',
                  snippet:
                      'Odjezd: ${ride['departure_time']}\nCena: ${ride['price_per_person']} Kč',
                  onTap: () => _showRideInfo(ride),
                ),
                icon: BitmapDescriptor.defaultMarkerWithHue(
                    BitmapDescriptor.hueGreen),
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
                icon: BitmapDescriptor.defaultMarkerWithHue(
                    BitmapDescriptor.hueRed),
              ),
            );

            // Add simple route line
            final routePoints = _buildRoutePoints(
              startCoords,
              endCoords,
              ride['route_waypoints'],
            );
            if (routePoints.length >= 2) {
              newPolylines.add(
                Polyline(
                  polylineId: PolylineId('ride_route_${ride['id']}'),
                  points: routePoints,
                  color: _getRouteColor(ride['id']),
                  width: 4,
                  patterns: [PatternItem.dash(20), PatternItem.gap(10)],
                ),
              );
            }
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
          SnackBar(
              content: Text('Chyba při načítání jízd: ${response.statusCode}')),
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
    final colors = [
      Colors.blue,
      Colors.red,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal
    ];
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
