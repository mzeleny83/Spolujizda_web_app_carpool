import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Spolujízda'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Text('Vítejte v aplikaci Spolujízda!', 
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 40),
            Expanded(
              child: GridView.count(
                crossAxisCount: 3,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                children: [
                  _buildMenuCard(
                    context,
                    'Nabídnout jízdu',
                    Icons.directions_car,
                    Colors.green,
                    '/offer',
                  ),
                  _buildMenuCard(
                    context,
                    'Hledat jízdu',
                    Icons.search,
                    Colors.blue,
                    '/simple',
                  ),
                  _buildMenuCard(
                    context,
                    'Moje shody',
                    Icons.people,
                    Colors.orange,
                    '/matches',
                  ),
                  _buildMenuCard(
                    context,
                    'Zprávy',
                    Icons.chat,
                    Colors.purple,
                    '/chat',
                  ),
                  _buildMenuCard(
                    context,
                    'Mapa řidičů',
                    Icons.map,
                    Colors.red,
                    '/map',
                  ),
                  _buildMenuCard(
                    context,
                    'Moji pasažéři',
                    Icons.star,
                    Colors.amber,
                    '/driver-reservations',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuCard(BuildContext context, String title, IconData icon, 
      Color color, String route) {
    return Card(
      elevation: 4,
      child: InkWell(
        onTap: () => Navigator.pushNamed(context, route),
        child: Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 48, color: color),
              const SizedBox(height: 8),
              Text(title, textAlign: TextAlign.center, 
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }
}