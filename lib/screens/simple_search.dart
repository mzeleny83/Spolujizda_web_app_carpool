import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SimpleSearchScreen extends StatefulWidget {
  @override
  _SimpleSearchScreenState createState() => _SimpleSearchScreenState();
}

class _SimpleSearchScreenState extends State<SimpleSearchScreen> {
  final _controller = TextEditingController();
  List<dynamic> _rides = [];
  bool _loading = false;

  Future<void> _search() async {
    setState(() { _loading = true; });
    
    try {
      final response = await http.get(
        Uri.parse('http://127.0.0.1:8080/api/rides/search?from=${_controller.text}'),
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
                    title: Text('${ride['from_location']} → ${ride['to_location']}'),
                    subtitle: Text('${ride['departure_time']} • ${ride['price_per_person']} Kč'),
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