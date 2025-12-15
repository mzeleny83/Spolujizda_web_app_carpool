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

  Widget _buildSeatBadge(int seatsAvailable, bool isMyRide) {
    final color = isMyRide ? Colors.indigo : Colors.teal;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        CircleAvatar(
          backgroundColor: color,
          radius: 28,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '$seatsAvailable',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
              const SizedBox(height: 2),
              const Text(
                'volno',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 11,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons({
    required Map<String, dynamic> ride,
    required int? rideId,
    required bool isMyRide,
    required bool isReserved,
  }) {
    if (isMyRide) {
      return SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: () => _deleteRide(rideId ?? 0, ride['title']),
          icon: const Icon(Icons.delete_outline),
          label: const Text('Smazat'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red,
            foregroundColor: Colors.white,
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (!isReserved)
          ElevatedButton.icon(
            onPressed: () => _reserveRide(ride),
            icon: const Icon(Icons.event_available),
            label: const Text('Rezervovat'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.teal,
              foregroundColor: Colors.white,
            ),
          )
        else
          Container(
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: const Chip(
              label: Text('Rezervovano'),
              backgroundColor: Colors.green,
              labelStyle: TextStyle(color: Colors.white),
            ),
          ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => _openChat(ride),
          icon: const Icon(Icons.chat),
          label: const Text('Chat'),
        ),
      ],
    );
  }

  Widget _addressRow(String label, String? value, IconData icon) {
    final display =
        (value ?? '').trim().isEmpty ? 'Neznama adresa' : value!.trim();
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
              maxLines: 4,
              softWrap: true,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade800,
                height: 1.3,
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
                final seatsAvailable = (ride['seats'] as num?)?.toInt() ??
                    (ride['available_seats'] as num?)?.toInt() ??
                    0;
                final isMyRide = ride['isMyRide'] == true;
                final isReserved =
                    rideId != null && _reservedRides.contains(rideId);

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 4.0),
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildSeatBadge(seatsAvailable, isMyRide),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    ride['title'],
                                    softWrap: true,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  _addressRow(
                                    'Odkud',
                                    ride['from_location'],
                                    Icons.location_on_outlined,
                                  ),
                                  _addressRow(
                                    'Kam',
                                    ride['to_location'],
                                    Icons.flag_outlined,
                                  ),
                                  const SizedBox(height: 6),
                                  Text('Ridic: ${ride['driver']}'),
                                  Text('Cas: ${ride['time']}'),
                                  Text(
                                    'Volna mista: $seatsAvailable | ${ride['price']} Kc',
                                  ),
                                  if (ride['note'] != null &&
                                      ride['note'].toString().isNotEmpty)
                                    Text('Poznamka: ${ride['note']}'),
                                  if (isMyRide)
                                    const Padding(
                                      padding: EdgeInsets.only(top: 4),
                                      child: Text(
                                        'Toto je vase jizda',
                                        style: TextStyle(
                                          color: Colors.indigo,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        _buildActionButtons(
                          ride: ride,
                          rideId: rideId,
                          isMyRide: isMyRide,
                          isReserved: isReserved,
                        ),
                      ],
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
