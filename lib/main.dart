import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spolujízda',
      home: SearchScreen(),
    );
  }
}

class SearchScreen extends StatefulWidget {
  @override
  _SearchScreenState createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _controller = TextEditingController();
  List<dynamic> _rides = [];
  bool _loading = false;

  Future<void> _search() async {
    setState(() { _loading = true; });
    
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8080/api/rides/search?from=${_controller.text}')
      );
      
      if (response.statusCode == 200) {
        setState(() {
          _rides = json.decode(response.body);
          _loading = false;
        });
      }
    } catch (e) {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Spolujízda - Hledat jízdy')),
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
                      hintText: 'Praha, Brno, Ostrava...',
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