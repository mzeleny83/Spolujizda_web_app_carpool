import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/offer_ride_screen.dart';
import 'screens/find_ride_screen.dart';
import 'screens/matches_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/map_screen.dart';

void main() {
  runApp(const SpolujizdaApp());
}

class SpolujizdaApp extends StatelessWidget {
  const SpolujizdaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spolujízda',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/home': (context) => const HomeScreen(),
        '/offer': (context) => const OfferRideScreen(),
        '/find': (context) => const FindRideScreen(),
        '/matches': (context) => const MatchesScreen(),
        '/chat': (context) => const ChatScreen(),
        '/map': (context) => const MapScreen(),
      },
    );
  }
}