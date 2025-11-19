import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../config/api_config.dart';

class SimpleSearchScreen extends StatefulWidget {
  const SimpleSearchScreen({super.key});
  
  @override
  _SimpleSearchScreenState createState() => _SimpleSearchScreenState();
}

class _SimpleSearchScreenState extends State<SimpleSearchScreen> {
  final _controller = TextEditingController();
  List<dynamic> _rides = [];
  bool _loading = false;

  Widget _addressRow(String label, String? value, IconData icon) {
    final text = (value ?? '').trim().isEmpty ? 'Neznámá adresa' : value!.trim();
    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Colors.grey.shade600),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              '$label: $text',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _search() async {
    setState(() { _loading = true; });
    
    try {
      final response = await http.get(
        ApiConfig.uri('/api/rides/search', query: {'from': _controller.text}),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        setState(() {
          _rides = json.decode(response.body);
          _loading = false;
        });
      }
    } catch (e) {
      setState(() { _loading = false; });
      print('Chyba: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Hledat jízdy')),
      body: Column(
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: 'Zadej město (Praha, Brno...)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _search,
                  child: Text('Hledat'),
                ),
              ],
            ),
          ),
          if (_loading) CircularProgressIndicator(),
          Expanded(
            child: ListView.builder(
              itemCount: _rides.length,
              itemBuilder: (context, index) {
                final ride = _rides[index];
                return Card(
                  margin: EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(
                      '${ride['from_location']} → ${ride['to_location']}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _addressRow('Odkud', ride['from_location'], Icons.location_on_outlined),
                        _addressRow('Kam', ride['to_location'], Icons.flag_outlined),
                        Text('Čas: ${ride['departure_time']}'),
                        Text('Cena: ${ride['price_per_person']} Kč | Volná místa: ${ride['available_seats']}'),
                      ],
                    ),
                    trailing: Text('${ride['available_seats']} míst'),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
