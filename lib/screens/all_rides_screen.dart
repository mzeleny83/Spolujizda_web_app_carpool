import 'package:flutter/material.dart';
import '../services/ride_service.dart';

class AllRidesScreen extends StatefulWidget {
  const AllRidesScreen({super.key});

  @override
  State<AllRidesScreen> createState() => _AllRidesScreenState();
}

class _AllRidesScreenState extends State<AllRidesScreen> {
  final RideService _rideService = RideService();
  Set<int> _reservedRides = {};

  Future<void> _reserveRide(Map<String, dynamic> ride) async {
    await _rideService.addReservation(ride);
    setState(() {
      _reservedRides.add(ride['id']);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✓ Jízda byla úspěšně zarezervována!'),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _openChat(Map<String, dynamic> ride) {
    Navigator.pushNamed(
      context,
      '/chat',
      arguments: {
        'contact_name': ride['driver'],
        'contact_phone': '+420602123456',
        'ride_info': ride['title'],
      },
    );
  }

  void _deleteRide(int rideId, String title) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Smazat jízdu'),
        content: Text('Opravdu chcete smazat jízdu $title?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Zrušit'),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                _rideService.deleteRide(rideId);
              });
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Jízda byla smazána')),
              );
            },
            child: const Text('Smazat', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
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
    final allRides = _rideService.getAllRides();

    if (allRides.isEmpty) {
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

    return ListView.builder(
      padding: const EdgeInsets.all(8.0),
      itemCount: allRides.length,
      itemBuilder: (context, index) {
        final ride = allRides[index];
        final isMyRide = ride['isMyRide'] == true;
        final isReserved = _reservedRides.contains(ride['id']);
        
        return Card(
          margin: const EdgeInsets.symmetric(vertical: 4.0),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: isMyRide ? Colors.indigo : Colors.teal,
              child: Text(
                '${ride['seats']}',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
            title: Text(
              ride['title'],
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text('Řidič: ${ride['driver']}'),
                Text('Čas: ${ride['time']}'),
                Text('Volná místa: ${ride['seats']} • ${ride['price']} Kč'),
                if (ride['note'] != null && ride['note'].toString().isNotEmpty)
                  Text('Poznámka: ${ride['note']}'),
                if (isMyRide)
                  const Text('🚗 Vaše jízda', style: TextStyle(color: Colors.indigo, fontWeight: FontWeight.bold)),
              ],
            ),
            trailing: isMyRide
                ? ElevatedButton(
                    onPressed: () => _deleteRide(ride['id'], ride['title']),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                    child: const Text('Smazat', style: TextStyle(color: Colors.white)),
                  )
                : isReserved
                    ? Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Chip(
                            label: Text('Rezervováno'),
                            backgroundColor: Colors.green,
                            labelStyle: TextStyle(color: Colors.white),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: () => _openChat(ride),
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                            child: const Text('Chat', style: TextStyle(color: Colors.white)),
                          ),
                        ],
                      )
                    : Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          ElevatedButton(
                            onPressed: () => _reserveRide(ride),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.teal,
                              foregroundColor: Colors.white,
                            ),
                            child: const Text('Rezervovat'),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: () => _openChat(ride),
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                            child: const Text('Chat', style: TextStyle(color: Colors.white)),
                          ),
                        ],
                      ),
          ),
        );
      },
    );
  }
}