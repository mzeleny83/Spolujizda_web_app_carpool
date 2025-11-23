import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';

class OSMMapScreen extends StatefulWidget {
  const OSMMapScreen({super.key});

  @override
  State<OSMMapScreen> createState() => _OSMMapScreenState();
}

class _OSMMapScreenState extends State<OSMMapScreen> {
  final MapController _mapController = MapController();
  List<Marker> _markers = [];
  List<Polyline> _polylines = [];
  LatLng? _userLocation;
  double _lastZoom = 7.0;
  bool _isLoading = true;

  static const LatLng _defaultCenter = LatLng(49.75, 15.5);

  // Real GPS coordinates for Czech cities
  final Map<String, LatLng> _cityCoordinates = {
    'Praha': const LatLng(50.0755, 14.4378),
    'Brno': const LatLng(49.1951, 16.6068),
    'Ostrava': const LatLng(49.8209, 18.2625),
    'Plzen': const LatLng(49.7384, 13.3736),
    'Ceske Budejovice': const LatLng(48.9745, 14.4743),
    'Liberec': const LatLng(50.7663, 15.0543),
  };

  @override
  void initState() {
    super.initState();
    _initMap();
  }

  Future<void> _initMap() async {
    await _getCurrentLocation();
    await _loadRides();
  }

  Future<void> _getCurrentLocation() async {
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _showMessage('Zapn�� geolokaci v nastaven�� telefonu.');
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.deniedForever) {
        _showMessage('Aplikace nem�� p��stup k poloze. Povol ji v nastaven��.');
        return;
      }

      if (permission == LocationPermission.whileInUse ||
          permission == LocationPermission.always) {
        Position? position;
        try {
          position = await Geolocator.getCurrentPosition(
            desiredAccuracy: LocationAccuracy.high,
          );
        } catch (_) {
          position = await Geolocator.getLastKnownPosition();
        }

        if (position != null) {
          final userPoint = LatLng(position.latitude, position.longitude);
          setState(() {
            _userLocation = userPoint;
          });
          _moveCameraTo(userPoint, zoom: 13);
        }
      }
    } catch (_) {
      // If location is unavailable we keep the default center
    }
  }

  void _moveCameraTo(LatLng target, {double? zoom}) {
    final nextZoom = zoom ?? _lastZoom;
    _lastZoom = nextZoom;
    try {
      _mapController.move(target, nextZoom);
    } catch (_) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        try {
          _mapController.move(target, nextZoom);
        } catch (_) {}
      });
    }
  }

  Future<void> _loadRides() async {
    setState(() {
      _isLoading = true;
      _markers.clear();
      _polylines.clear();
    });

    try {
      final response = await http.get(ApiConfig.uri('/api/rides/search'));

      if (response.statusCode == 200) {
        final List<dynamic> ridesData = json.decode(response.body);
        final List<Marker> newMarkers = [];
        final List<Polyline> newPolylines = [];

        if (_userLocation != null) {
          newMarkers.add(
            Marker(
              point: _userLocation!,
              width: 38,
              height: 38,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.blue.shade600,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 3),
                  boxShadow: const [
                    BoxShadow(
                      color: Colors.black26,
                      blurRadius: 4,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.my_location,
                  color: Colors.white,
                  size: 18,
                ),
              ),
            ),
          );
        }

        for (var ride in ridesData) {
          final String fromLocation = ride['from_location'];
          final String toLocation = ride['to_location'];

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
                    child: const Icon(
                      Icons.directions_car,
                      color: Colors.white,
                      size: 20,
                    ),
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
                    child: const Icon(
                      Icons.location_on,
                      color: Colors.white,
                      size: 20,
                    ),
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
      } else {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Chyba pri nacitani jizd: ${response.statusCode}'),
          ),
        );
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba pri nacitani jizd: $e')),
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
                'Vsechny dostupne jizdy',
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
                      return Center(
                        child: Text('Chyba: ${snapshot.error}'),
                      );
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
                              child: const Icon(
                                Icons.directions_car,
                                color: Colors.white,
                              ),
                            ),
                            title: Text(
                              '${ride['from_location']} -> ${ride['to_location']}',
                            ),
                            subtitle: Text(
                              'Ridic: ${ride['driver_name']}\n'
                              'Cas: ${ride['departure_time']}\n'
                              'Cena: ${ride['price_per_person']} Kc | '
                              'Mista: ${ride['available_seats']}',
                            ),
                            isThreeLine: true,
                            onTap: () {
                              Navigator.pop(context);
                              _showRideInfo(ride);
                              final startCoords =
                                  _cityCoordinates[ride['from_location']];
                              final endCoords =
                                  _cityCoordinates[ride['to_location']];
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
      final response = await http.get(ApiConfig.uri('/api/rides/search'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {
      // Ignore errors here; handled by callers
    }
    return [];
  }

  Future<void> _reserveRide(Map<String, dynamic> ride) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id') ?? 1;
      
      final response = await http.post(
        ApiConfig.uri('/api/rides/reserve'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ride_id': ride['id'],
          'passenger_id': userId,
          'seats_reserved': 1,
        }),
      );
      
      Navigator.pop(context);
      
      if (response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Jizda byla uspesne zarezervovana!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        final data = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(data['error'] ?? 'Chyba pri rezervaci')),
        );
      }
    } catch (e) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba pripojeni: $e')),
      );
    }
  }

  void _showRideInfo(Map<String, dynamic> ride) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => SafeArea(
        child: Container(
          padding: const EdgeInsets.all(16),
          margin: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom + 16,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Jizda s ${ride['driver_name'] ?? 'Neznamy ridic'}',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              Text('Trasa: ${ride['from_location']} -> ${ride['to_location']}'),
              Text('Cas odjezdu: ${ride['departure_time']}'),
              Text('Volna mista: ${ride['available_seats']}'),
              Text('Cena: ${ride['price_per_person']} Kc'),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/chat', arguments: {
                        'contact_name': ride['driver_name'],
                        'contact_phone':
                            ride['driver_phone'] ?? '+420721745084',
                        'ride_info':
                            '${ride['from_location']} -> ${ride['to_location']}',
                      });
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Chat'),
                  ),
                  ElevatedButton(
                    onPressed: () => _reserveRide(ride),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Rezervovat'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final initialCenter = _userLocation ?? _defaultCenter;
    final initialZoom = _userLocation != null ? 13.0 : _lastZoom;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mapa jizd (OpenStreetMap)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: _showAllRides,
            tooltip: 'Vsechny jizdy',
          ),
          IconButton(
            icon: const Icon(Icons.my_location),
            onPressed: () {
              if (_userLocation != null) {
                _moveCameraTo(_userLocation!, zoom: 13);
              } else {
                _getCurrentLocation();
              }
            },
            tooltip: 'Moje poloha',
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
              options: MapOptions(
                initialCenter: initialCenter,
                initialZoom: initialZoom,
                minZoom: 6.0,
                maxZoom: 18.0,
                onMapReady: () {
                  if (_userLocation != null) {
                    _moveCameraTo(_userLocation!, zoom: 13);
                  }
                },
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
