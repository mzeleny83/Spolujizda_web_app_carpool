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
      final to = arguments?['to'] ?? '';
      
      // Sestavení URL s parametry
      String url = 'https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/search';
      List<String> params = [];
      
      if (from.isNotEmpty) {
        params.add('from=${Uri.encodeComponent(from)}');
      }
      if (to.isNotEmpty) {
        params.add('to=${Uri.encodeComponent(to)}');
      }
      
      if (params.isNotEmpty) {
        url += '?' + params.join('&');
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

  Widget _buildRatingStars(double rating) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (index) {
        return Icon(
          index < rating.floor() ? Icons.star : 
          index < rating ? Icons.star_half : Icons.star_border,
          color: Colors.amber,
          size: 20,
        );
      }),
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
                _buildRatingStars(ride['driver_rating']?.toDouble() ?? 5.0),
                const SizedBox(height: 4),
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