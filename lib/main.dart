import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/find_ride_screen.dart';
import 'screens/offer_ride_screen.dart';
import 'screens/matches_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/map_screen.dart';
import 'screens/simple_map_screen.dart';
import 'screens/basic_map_screen.dart';
import 'screens/simple_search.dart';
import 'screens/rating_screen.dart';
import 'screens/driver_reservations_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spolujízda',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/home': (context) => const HomeScreen(),
        '/find': (context) => const FindRideScreen(),
        '/offer': (context) => const OfferRideScreen(),
        '/matches': (context) => const MatchesScreen(),
        '/chat': (context) => const ChatScreen(),
        '/map': (context) => const BasicMapScreen(),
        '/simple': (context) => const SimpleSearchScreen(),
        '/rating': (context) => const RatingScreen(),
        '/driver-reservations': (context) => const DriverReservationsScreen(),
      },
    );
  }
}