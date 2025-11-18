import 'package:flutter/material.dart';
import '../services/ride_service.dart';

class AllReservationsScreen extends StatefulWidget {
  const AllReservationsScreen({super.key});

  @override
  State<AllReservationsScreen> createState() => _AllReservationsScreenState();
}

class _AllReservationsScreenState extends State<AllReservationsScreen> {
  final RideService _rideService = RideService();

  @override
  void initState() {
    super.initState();
    // Přidáme listener pro aktualizace
    WidgetsBinding.instance.addPostFrameCallback((_) {
      setState(() {}); // Refresh při načtení
    });
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Moje jízdy'),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () => setState(() {}),
            ),
          ],
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [
              Tab(icon: Icon(Icons.event_seat), text: 'Moje rezervace'),
              Tab(icon: Icon(Icons.directions_car), text: 'Mnou nabízené'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildReservations(),
            _buildOfferedRides(),
          ],
        ),
      ),
    );
  }

  Widget _buildReservations() {
    final myReservations = _rideService.getMyReservations();
    
    if (myReservations.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_seat_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Nemáte žádné rezervace jízd.'),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: myReservations.length,
      itemBuilder: (context, index) {
        final reservation = myReservations[index];
        return Card(
          margin: const EdgeInsets.all(8.0),
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: Colors.blue,
              child: Icon(Icons.event_seat, color: Colors.white),
            ),
            title: Text(reservation['title']),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Řidič: ${reservation['driver']}'),
                Text('Čas: ${reservation['time']}'),
                Text('Cena: ${reservation['price']} Kč'),
              ],
            ),
            trailing: ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(
                  context,
                  '/chat',
                  arguments: {
                    'contact_name': reservation['driver'],
                    'contact_phone': '+420602123456',
                    'ride_info': reservation['title'],
                  },
                );
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
              child: const Text('Chat', style: TextStyle(color: Colors.white)),
            ),
          ),
        );
      },
    );
  }

  Widget _buildOfferedRides() {
    final myRides = _rideService.getMyRides();
    
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(8.0),
          color: Colors.blue.shade50,
          child: Row(
            children: [
              const Icon(Icons.info, color: Colors.blue),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Celkem jízd: ${myRides.length}. Klikněte na refresh pro aktualizaci.',
                  style: const TextStyle(color: Colors.blue),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: myRides.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.directions_car_outlined, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('Nemáte žádné jízdy, které nabízíte.'),
                      SizedBox(height: 8),
                      Text('Nabídněte jízdu přes "Nabídnout jízdu"', 
                           style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: myRides.length,
                  itemBuilder: (context, index) {
                    final ride = myRides[index];
                    return Card(
                      margin: const EdgeInsets.all(8.0),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.green,
                          child: Text('${ride['seats']}', 
                                     style: const TextStyle(color: Colors.white)),
                        ),
                        title: Text(ride['title']),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Čas: ${ride['time']}'),
                            Text('Volná místa: ${ride['seats']} • ${ride['price']} Kč'),
                            Text('Poznámka: ${ride['note']}'),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            ElevatedButton(
                              onPressed: () {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Jízda ${ride['title']} je aktivní')),
                                );
                              },
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                              child: const Text('Aktivní', style: TextStyle(color: Colors.white)),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              onPressed: () => _deleteRide(index),
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                              child: const Text('Smazat', style: TextStyle(color: Colors.white)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  void _deleteRide(int index) {
    final myRides = _rideService.getMyRides();
    final rideId = myRides[index]['id'];
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Smazat jízdu'),
        content: Text('Opravdu chcete smazat jízdu ${myRides[index]['title']}?'),
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
}