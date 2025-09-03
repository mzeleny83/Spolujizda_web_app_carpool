import 'package:flutter/material.dart';

class MatchesScreen extends StatelessWidget {
  const MatchesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final matches = [
      {'name': 'Jan Novák', 'from': 'Brno', 'to': 'Praha', 'time': '08:00', 'price': '200 Kč'},
      {'name': 'Marie Svobodová', 'from': 'Ostrava', 'to': 'Brno', 'time': '07:30', 'price': '150 Kč'},
      {'name': 'Petr Dvořák', 'from': 'Praha', 'to': 'Plzeň', 'time': '09:00', 'price': '180 Kč'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Nalezené jízdy')),
      body: ListView.builder(
        itemCount: matches.length,
        itemBuilder: (context, index) {
          final match = matches[index];
          return Card(
            margin: const EdgeInsets.all(8.0),
            child: ListTile(
              leading: const CircleAvatar(
                child: Icon(Icons.person),
              ),
              title: Text(match['name']!),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${match['from']} → ${match['to']}'),
                  Text('Čas: ${match['time']} | Cena: ${match['price']}'),
                ],
              ),
              trailing: ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(context, '/chat');
                },
                child: const Text('Kontakt'),
              ),
            ),
          );
        },
      ),
    );
  }
}