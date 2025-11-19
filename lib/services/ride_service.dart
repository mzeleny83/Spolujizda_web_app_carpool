import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class RideService {
  static final RideService _instance = RideService._internal();
  factory RideService() => _instance;
  RideService._internal() {
    _loadReservations();
  }

  List<Map<String, dynamic>> _reservations = [];
  
  List<Map<String, dynamic>> _allRides = [
    {
      'id': 1,
      'title': 'Brno → Zlín',
      'time': '2025-11-19 14:00',
      'seats': 3,
      'price': 150,
      'note': 'Pohodová jízda do Zlína',
      'driver': 'Miroslav Zelený',
      'isMyRide': true,
    },
    {
      'id': 2,
      'title': 'Praha → Ostrava',
      'time': '2025-11-20 08:00',
      'seats': 2,
      'price': 300,
      'note': 'Rychlá jízda na východ',
      'driver': 'Miroslav Zelený',
      'isMyRide': true,
    },
    {
      'id': 3,
      'title': 'Praha → Brno',
      'time': '2025-11-18 15:00',
      'seats': 3,
      'price': 200,
      'note': 'Pohodová jízda',
      'driver': 'Jan Novák',
      'isMyRide': false,
    },
    {
      'id': 4,
      'title': 'Brno → Praha',
      'time': '2025-11-18 17:30',
      'seats': 2,
      'price': 250,
      'note': 'Rychlá jízda',
      'driver': 'Marie Svobodová',
      'isMyRide': false,
    },
  ];

  List<Map<String, dynamic>> getAllRides() => List.from(_allRides);
  
  List<Map<String, dynamic>> getMyRides() => 
      _allRides.where((ride) => ride['isMyRide'] == true).toList();
  
  List<Map<String, dynamic>> getMyReservations() => List.from(_reservations);
  
  void addRide(Map<String, dynamic> ride) {
    ride['id'] = _allRides.length + 100;
    ride['isMyRide'] = true;
    ride['driver'] = 'Miroslav Zelený';
    _allRides.add(ride);
  }
  
  Future<void> _loadReservations() async {
    final prefs = await SharedPreferences.getInstance();
    final reservationsJson = prefs.getString('reservations');
    if (reservationsJson != null) {
      final List<dynamic> decoded = jsonDecode(reservationsJson);
      _reservations = decoded.cast<Map<String, dynamic>>();
    }
  }
  
  Future<void> _saveReservations() async {
    final prefs = await SharedPreferences.getInstance();
    final reservationsJson = jsonEncode(_reservations);
    await prefs.setString('reservations', reservationsJson);
  }
  
  Future<void> addReservation(Map<String, dynamic> ride) async {
    final reservation = {
      'id': _reservations.length + 1,
      'title': ride['title'],
      'time': ride['time'],
      'driver': ride['driver'],
      'seats': 1,
      'price': ride['price'],
      'note': 'Rezervováno z aplikace',
    };
    _reservations.add(reservation);
    await _saveReservations();
  }
  
  void deleteRide(int id) {
    _allRides.removeWhere((ride) => ride['id'] == id);
  }
}