import 'package:flutter/material.dart';

class TestScreen extends StatelessWidget {
  const TestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('TEST - Moje jízdy'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        children: [
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text(
              'TESTOVACÍ OBRAZOVKA - Nabízené jízdy:',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          Card(
            margin: const EdgeInsets.all(8.0),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Colors.green,
                child: Text('3', style: TextStyle(color: Colors.white)),
              ),
              title: const Text('Brno → Zlín'),
              subtitle: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Čas: 2025-11-19 14:00'),
                  Text('Volná místa: 3 • 150 Kč'),
                  Text('Poznámka: Pohodová jízda do Zlína'),
                ],
              ),
              trailing: ElevatedButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Jízda Brno → Zlín je aktivní')),
                  );
                },
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                child: const Text('Aktivní', style: TextStyle(color: Colors.white)),
              ),
            ),
          ),
          Card(
            margin: const EdgeInsets.all(8.0),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Colors.green,
                child: Text('2', style: TextStyle(color: Colors.white)),
              ),
              title: const Text('Praha → Ostrava'),
              subtitle: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Čas: 2025-11-20 08:00'),
                  Text('Volná místa: 2 • 300 Kč'),
                  Text('Poznámka: Rychlá jízda na východ'),
                ],
              ),
              trailing: ElevatedButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Jízda Praha → Ostrava je aktivní')),
                  );
                },
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                child: const Text('Aktivní', style: TextStyle(color: Colors.white)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}