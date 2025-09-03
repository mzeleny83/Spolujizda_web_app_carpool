import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  GoogleMapController? mapController;
  LatLng _currentPosition = const LatLng(49.1951, 16.6068); // Brno
  Set<Marker> _markers = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
    _loadDrivers();
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

  void _loadDrivers() {
    // Simulace řidičů v okolí
    final drivers = [
      {'name': 'Jan Novák', 'lat': 49.2000, 'lng': 16.6100},
      {'name': 'Marie Svobodová', 'lat': 49.1900, 'lng': 16.6000},
      {'name': 'Petr Dvořák', 'lat': 49.1950, 'lng': 16.6150},
    ];

    Set<Marker> markers = {};
    for (var driver in drivers) {
      markers.add(
        Marker(
          markerId: MarkerId(driver['name'] as String),
          position: LatLng(driver['lat'] as double, driver['lng'] as double),
          infoWindow: InfoWindow(
            title: driver['name'] as String,
            snippet: 'Dostupný řidič',
            onTap: () => _showDriverInfo(driver['name'] as String),
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
        ),
      );
    }

    // Přidání vlastní pozice
    markers.add(
      Marker(
        markerId: const MarkerId('my_location'),
        position: _currentPosition,
        infoWindow: const InfoWindow(title: 'Moje poloha'),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
      ),
    );

    setState(() => _markers = markers);
  }

  void _showDriverInfo(String driverName) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(driverName, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            const Text('Trasa: Brno → Praha'),
            const Text('Čas odjezdu: 08:00'),
            const Text('Volná místa: 2'),
            const Text('Cena: 200 Kč'),
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
        title: const Text('Mapa řidičů'),
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