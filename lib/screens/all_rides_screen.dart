import 'package:flutter/material.dart';

import '../services/ride_service.dart';

class AllRidesScreen extends StatefulWidget {
  const AllRidesScreen({super.key});

  @override
  State<AllRidesScreen> createState() => _AllRidesScreenState();
}

class _AllRidesScreenState extends State<AllRidesScreen> {
  final RideService _rideService = RideService();
  late Future<List<Map<String, dynamic>>> _ridesFuture;
  Set<int> _reservedRides = {};

  @override
  void initState() {
    super.initState();
    _ridesFuture = _rideService.fetchAllRides();
    _loadReservations();
  }

  Future<void> _loadReservations() async {
    try {
      final reservations =
          await _rideService.fetchReservations(forceRefresh: true);
      if (!mounted) return;
      setState(() {
        _reservedRides = reservations
            .map<int?>((reservation) {
              final rideId = reservation['ride_id'] ?? reservation['id'];
              if (rideId is int) return rideId;
              if (rideId is num) return rideId.toInt();
              return int.tryParse(rideId?.toString() ?? '');
            })
            .whereType<int>()
            .toSet();
      });
    } catch (error) {
      debugPrint('Nepodařilo se načíst rezervace: $error');
    }
  }

  Future<void> _reserveRide(Map<String, dynamic> ride) async {
    try {
      await _rideService.addReservation(ride);
      await _loadReservations();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Jízda byla úspěšně zarezervována.'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Rezervace se nezdařila: $error'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _refreshRides({bool force = false}) async {
    setState(() {
      _ridesFuture = _rideService.fetchAllRides(forceRefresh: force);
    });
    await _ridesFuture;
  }

  void _openChat(Map<String, dynamic> ride) {
    Navigator.pushNamed(
      context,
      '/chat',
      arguments: {
        'contact_name': ride['driver'],
        'contact_phone': ride['driver_phone'] ?? '+420602123456',
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
                _ridesFuture = Future.value(_rideService.getAllRides());
              });
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Jízda byla smazána.')),
              );
            },
            child: const Text('Smazat', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Widget _addressRow(String label, String? value, IconData icon) {
    final display =
        (value ?? '').trim().isEmpty ? 'Neznámá adresa' : value!.trim();
    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: Colors.grey.shade600),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              '$label: $display',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey.shade800,
                height: 1.2,
              ),
            ),
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
      body: RefreshIndicator(
        onRefresh: () async {
          await _refreshRides(force: true);
          await _loadReservations();
        },
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _ridesFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(
                    height: 200,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ],
              );
            }

            if (snapshot.hasError) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      children: [
                        const Icon(Icons.error_outline,
                            size: 48, color: Colors.red),
                        const SizedBox(height: 12),
                        Text(
                          'Nepodařilo se načíst jízdy: ${snapshot.error}',
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ],
              );
            }

            final rides = snapshot.data ?? [];
            if (rides.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 60),
                  Icon(Icons.directions_car_outlined,
                      size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Center(
                    child: Text('Momentálně nejsou k dispozici žádné jízdy.'),
                  ),
                ],
              );
            }

            return ListView.builder(
              padding: const EdgeInsets.all(8.0),
              itemCount: rides.length,
              itemBuilder: (context, index) {
                final ride = rides[index];
                final rideId = (ride['id'] as num?)?.toInt();
                final isMyRide = ride['isMyRide'] == true;
                final isReserved =
                    rideId != null && _reservedRides.contains(rideId);

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 4.0),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isMyRide ? Colors.indigo : Colors.teal,
                      child: Text(
                        '${ride['seats']}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      ride['title'],
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        _addressRow('Odkud', ride['from_location'],
                            Icons.location_on_outlined),
                        _addressRow('Kam', ride['to_location'],
                            Icons.flag_outlined),
                        const SizedBox(height: 4),
                        Text(
                          'Řidič: ${ride['driver']}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          'Čas: ${ride['time']}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          'Volná místa: ${ride['seats']} • ${ride['price']} Kč',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (ride['note'] != null &&
                            ride['note'].toString().isNotEmpty)
                          Text(
                            'Poznámka: ${ride['note']}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        if (isMyRide)
                          const Text(
                            '✅ Vaše jízda',
                            style: TextStyle(
                              color: Colors.indigo,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                      ],
                    ),
                    trailing: SizedBox(
                      width: 140,
                      child: isMyRide
                          ? ElevatedButton(
                              onPressed: () =>
                                  _deleteRide(rideId ?? 0, ride['title']),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.red,
                              ),
                              child: const Text(
                                'Smazat',
                                style: TextStyle(color: Colors.white),
                              ),
                            )
                          : Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: [
                                if (!isReserved)
                                  SizedBox(
                                    width: 130,
                                    child: ElevatedButton(
                                      onPressed: () => _reserveRide(ride),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.teal,
                                        foregroundColor: Colors.white,
                                      ),
                                      child: const Text('Rezervovat'),
                                    ),
                                  )
                                else
                                  const Chip(
                                    label: Text('Rezervováno'),
                                    backgroundColor: Colors.green,
                                    labelStyle:
                                        TextStyle(color: Colors.white),
                                  ),
                                SizedBox(
                                  width: 130,
                                  child: ElevatedButton(
                                    onPressed: () => _openChat(ride),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.blue,
                                    ),
                                    child: const Text(
                                      'Chat',
                                      style: TextStyle(color: Colors.white),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
