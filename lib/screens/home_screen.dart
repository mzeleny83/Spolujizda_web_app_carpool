import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _userInfo = 'Načítám...';

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
  }

  Future<void> _loadUserInfo() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');
    final userName = prefs.getString('user_name');
    final userRating = prefs.getDouble('user_rating');
    
    setState(() {
      _userInfo = 'ID: $userId | Jméno: $userName | Hodnocení: $userRating';
    });
    
    print('DEBUG HomeScreen - User ID: $userId, Name: $userName, Rating: $userRating');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Spolujízda'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              await prefs.clear();
              Navigator.pushReplacementNamed(context, '/guest-home');
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Text('Vítejte v aplikaci Spolujízda!', 
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Text(_userInfo, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 24),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 20,
                mainAxisSpacing: 20,
                childAspectRatio: 1.1,
                children: [
                  _buildMenuCard(
                    context,
                    'Moje jízdy',
                    Icons.person,
                    Colors.indigo,
                    '/all-reservations',
                  ),
                  _buildMenuCard(
                    context,
                    'Nabídnout jízdu',
                    Icons.add_circle,
                    Colors.green,
                    '/offer',
                  ),
                  _buildMenuCard(
                    context,
                    'Mapa jízd',
                    Icons.map,
                    Colors.red,
                    '/map',
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
                    'Všechny dostupné jízdy',
                    Icons.list_alt,
                    Colors.teal,
                    '/all-rides',
                  ),
                  _buildMenuCard(
                    context,
                    'Zprávy',
                    Icons.chat,
                    Colors.purple,
                    '/chat',
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
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis),
            ],
          ),
        ),
      ),
    );
  }
}