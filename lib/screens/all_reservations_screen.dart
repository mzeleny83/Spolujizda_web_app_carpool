import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class AllReservationsScreen extends StatefulWidget {
  const AllReservationsScreen({super.key});

  @override
  State<AllReservationsScreen> createState() => _AllReservationsScreenState();
}

class _AllReservationsScreenState extends State<AllReservationsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _myReservations = [];
  List<dynamic> _othersReservations = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchAllReservations();
  }

  Future<void> _fetchAllReservations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id') ?? 1;
      
      // Načtení mých rezervací
      final myReservationsResponse = await http.get(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/reservations?user_id=$userId'),
      );

      // Načtení všech rezervací (simulace - v reálné aplikaci by byl speciální endpoint)
      final allReservationsResponse = await http.get(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/reservations/all'),
      );

      if (myReservationsResponse.statusCode == 200) {
        final myData = json.decode(utf8.decode(myReservationsResponse.bodyBytes));
        
        // Simulace rezervací u mých jízd (v reálné aplikaci by to bylo z backendu)
        final othersData = [
          {
            'id': 101,
            'ride_id': 1,
            'passenger_name': 'Jan Novák',
            'seats_reserved': 2,
            'status': 'confirmed',
            'created_at': '2025-11-18 14:30:00',
            'ride_info': 'Praha → Brno'
          },
          {
            'id': 102,
            'ride_id': 2,
            'passenger_name': 'Marie Svobodová',
            'seats_reserved': 1,
            'status': 'confirmed',
            'created_at': '2025-11-18 15:45:00',
            'ride_info': 'Brno → Ostrava'
          }
        ];
        
        setState(() {
          _myReservations = myData;
          _othersReservations = othersData;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nepodařilo se načíst rezervace. Kód: ${myReservationsResponse.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Chyba připojení: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Všechny rezervace'),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(icon: Icon(Icons.person), text: 'Moje rezervace'),
            Tab(icon: Icon(Icons.group), text: 'U mých jízd'),
          ],
        ),
      ),
      body: _isLoading ? _buildLoading() : _buildTabView(),
    );
  }

  Widget _buildLoading() {
    return const Center(child: CircularProgressIndicator());
  }

  Widget _buildTabView() {
    if (_error != null) {
      return _buildError();
    }

    return TabBarView(
      controller: _tabController,
      children: [
        _buildMyReservations(),
        _buildOthersReservations(),
      ],
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _isLoading = true;
                _error = null;
              });
              _fetchAllReservations();
            },
            child: const Text('Zkusit znovu'),
          ),
        ],
      ),
    );
  }

  Widget _buildMyReservations() {
    if (_myReservations.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_seat_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Nemáte žádné rezervace.'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchAllReservations,
      child: ListView.builder(
        padding: const EdgeInsets.all(8.0),
        itemCount: _myReservations.length,
        itemBuilder: (context, index) {
          final reservation = _myReservations[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.blue,
                child: Text(
                  '${reservation['seats_reserved']}',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text('Rezervace #${reservation['id']}'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${reservation['seats_reserved']} místo • ${reservation['status']}'),
                  Text('Vytvořeno: ${reservation['created_at']}'),
                ],
              ),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
          );
        },
      ),
    );
  }

  Widget _buildOthersReservations() {
    if (_othersReservations.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.group_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Nikdo si zatím nezarezervoval vaše jízdy.'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchAllReservations,
      child: ListView.builder(
        padding: const EdgeInsets.all(8.0),
        itemCount: _othersReservations.length,
        itemBuilder: (context, index) {
          final reservation = _othersReservations[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.green,
                child: Text(
                  (reservation['passenger_name'] ?? 'N')[0].toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text(reservation['passenger_name'] ?? 'Neznámý cestující'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${reservation['ride_info']} • ${reservation['seats_reserved']} místo'),
                  Text('Rezervováno: ${reservation['created_at']}'),
                  Text('Status: ${reservation['status']}'),
                ],
              ),
              trailing: ElevatedButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Kontakt bude brzy k dispozici')),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                ),
                child: const Text('Kontakt'),
              ),
            ),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }
}