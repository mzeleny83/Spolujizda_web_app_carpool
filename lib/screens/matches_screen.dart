import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class MatchesScreen extends StatefulWidget {
  const MatchesScreen({super.key});

  @override
  State<MatchesScreen> createState() => _MatchesScreenState();
}

class _MatchesScreenState extends State<MatchesScreen> {
  List<dynamic> _rides = [];
  bool _isLoading = true;
  String? _error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _fetchRides();
  }

  Future<void> _fetchRides() async {
    try {
      final arguments = ModalRoute.of(context)!.settings.arguments as Map<String, String?>?;
      final from = arguments?['from'] ?? '';
      
      // Use the correct API endpoint - if no search term, get all rides
      String url;
      if (from.isEmpty) {
        url = 'http://localhost:8080/api/rides/all';
      } else {
        url = 'http://localhost:8080/api/rides/search?from=$from';
      }
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
            _rides = data;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to load rides. Status code: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'An error occurred: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nalezené jízdy')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!));
    }

    if (_rides.isEmpty) {
      return const Center(child: Text('Nebyly nalezeny žádné jízdy.'));
    }

    return ListView.builder(
      itemCount: _rides.length,
      itemBuilder: (context, index) {
        final ride = _rides[index];
        return Card(
          margin: const EdgeInsets.all(8.0),
          child: ListTile(
            leading: const CircleAvatar(
              child: Icon(Icons.person),
            ),
            title: Text(ride['driver_name'] ?? 'Neznámý řidič'),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${ride['from_location']} → ${ride['to_location']}'),
                Text('Čas: ${ride['departure_time']} | Cena: ${ride['price_per_person']} Kč'),
              ],
            ),
            trailing: ElevatedButton(
              onPressed: () {
                // Navigate to chat or ride details
                Navigator.pushNamed(context, '/chat');
              },
              child: const Text('Kontakt'),
            ),
          ),
        );
      },
    );
  }
}