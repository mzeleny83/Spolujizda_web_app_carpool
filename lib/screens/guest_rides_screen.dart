import 'package:flutter/material.dart';
import '../services/ride_service.dart';

class GuestRidesScreen extends StatefulWidget {
  const GuestRidesScreen({super.key});

  @override
  State<GuestRidesScreen> createState() => _GuestRidesScreenState();
}

class _GuestRidesScreenState extends State<GuestRidesScreen> {
  final RideService _rideService = RideService();
  late Future<List<Map<String, dynamic>>> _ridesFuture;

  @override
  void initState() {
    super.initState();
    _ridesFuture = _rideService.fetchAllRides();
  }

  void _showLoginPrompt(String action) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Přihlášení vyžadováno'),
        content: Text('Pro $action se musíte přihlásit.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Zrušit'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/login');
            },
            child: const Text('Přihlásit se'),
          ),
        ],
      ),
    );
  }

  Widget _buildSeatBadge(int seatsAvailable) {
    return CircleAvatar(
      backgroundColor: Colors.grey.shade400,
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
    );
  }

  Widget _buildGuestActionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton.icon(
          onPressed: () => _showLoginPrompt('rezervaci jízdy'),
          icon: const Icon(Icons.lock),
          label: const Text('Rezervovat (vyžaduje přihlášení)'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.grey.shade400,
            foregroundColor: Colors.white,
          ),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => _showLoginPrompt('chat s řidičem'),
          icon: const Icon(Icons.lock),
          label: const Text('Chat (vyžaduje přihlášení)'),
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  Widget _addressRow(String label, String? value, IconData icon) {
    final display = (value ?? '').trim().isEmpty ? 'Neznámá adresa' : value!.trim();
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
        title: const Text('Dostupné jízdy - Demo'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: () => Navigator.pushNamed(context, '/login'),
            child: const Text('Přihlásit se', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            color: Colors.orange.shade100,
            child: Row(
              children: [
                Icon(Icons.info_outline, color: Colors.orange.shade700),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Demo režim: Pro rezervaci a komunikaci se přihlaste',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<List<Map<String, dynamic>>>(
              future: _ridesFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (snapshot.hasError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.red),
                        const SizedBox(height: 12),
                        Text(
                          'Nepodařilo se načíst jízdy: ${snapshot.error}',
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                }

                final rides = snapshot.data ?? [];
                if (rides.isEmpty) {
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
                  itemCount: rides.length,
                  itemBuilder: (context, index) {
                    final ride = rides[index];
                    final seatsAvailable = (ride['seats'] as num?)?.toInt() ??
                        (ride['available_seats'] as num?)?.toInt() ??
                        0;

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
                                _buildSeatBadge(seatsAvailable),
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
                                      Text('Řidič: ${ride['driver']}'),
                                      Text('Čas: ${ride['time']}'),
                                      Text(
                                        'Volná místa: $seatsAvailable | ${ride['price']} Kč',
                                      ),
                                      if (ride['note'] != null &&
                                          ride['note'].toString().isNotEmpty)
                                        Text('Poznámka: ${ride['note']}'),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            _buildGuestActionButtons(),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}