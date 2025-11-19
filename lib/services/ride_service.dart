import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';

class RideService {
  static final RideService _instance = RideService._internal();
  factory RideService() => _instance;

  RideService._internal() {
    _loadReservations();
  }

  List<Map<String, dynamic>> _reservations = [];
  List<Map<String, dynamic>> _allRides = [];
  DateTime? _lastRideRefresh;
  bool _reservationsLoaded = false;

  Future<List<Map<String, dynamic>>> fetchAllRides({
    bool forceRefresh = false,
  }) async {
    final needsRefresh = forceRefresh ||
        _allRides.isEmpty ||
        _lastRideRefresh == null ||
        DateTime.now().difference(_lastRideRefresh!) >
            const Duration(minutes: 2);

    if (!needsRefresh) {
      return getAllRides();
    }

    final response = await http.get(ApiConfig.uri('/api/rides/search'));

    if (response.statusCode != 200) {
      throw Exception(
        'Nepodařilo se načíst jízdy (kód ${response.statusCode}).',
      );
    }

    final List<dynamic> decoded = jsonDecode(response.body) as List<dynamic>;
    final prefs = await SharedPreferences.getInstance();
    final currentUserId = prefs.getInt('user_id');

    _allRides = decoded
        .map<Map<String, dynamic>>(
          (ride) => _mapRide(
            Map<String, dynamic>.from(ride as Map),
            currentUserId,
          ),
        )
        .toList();
    _lastRideRefresh = DateTime.now();
    return getAllRides();
  }

  List<Map<String, dynamic>> getAllRides() =>
      List<Map<String, dynamic>>.from(_allRides);

  List<Map<String, dynamic>> getMyRides() =>
      _allRides.where((ride) => ride['isMyRide'] == true).toList();

  List<Map<String, dynamic>> getMyReservations() =>
      List<Map<String, dynamic>>.from(_reservations);

  Future<void> addRide(Map<String, dynamic> ride) async {
    final prefs = await SharedPreferences.getInstance();
    final driverId = prefs.getInt('user_id');

    if (driverId == null) {
      throw Exception('Nejprve se přihlaste, abyste mohli nabízet jízdy.');
    }

    final payload = {
      'driver_id': driverId,
      'from_location': ride['from_location'] ?? '',
      'to_location': ride['to_location'] ?? '',
      'departure_time': ride['departure_time'] ?? ride['time'],
      'available_seats': ride['available_seats'] ?? ride['seats'] ?? 1,
      'price': ride['price'] ?? 0,
      'description': ride['description'] ?? ride['note'] ?? '',
    };

    final response = await http.post(
      ApiConfig.uri('/api/rides/offer'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );

    if (response.statusCode >= 300) {
      final body = response.body.isNotEmpty
          ? jsonDecode(response.body) as Map<String, dynamic>
          : null;
      throw Exception(body?['error'] ?? 'Nabídku jízdy se nepodařilo uložit.');
    }

    await fetchAllRides(forceRefresh: true);
  }

  Future<void> addReservation(
    Map<String, dynamic> ride, {
    int seats = 1,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final passengerId = prefs.getInt('user_id');

    if (passengerId == null) {
      throw Exception('Nejprve se přihlaste, abyste mohli rezervovat jízdy.');
    }

    final response = await http.post(
      ApiConfig.uri('/api/rides/reserve'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'ride_id': ride['id'],
        'passenger_id': passengerId,
        'seats_reserved': seats,
      }),
    );

    if (response.statusCode >= 300) {
      final body = response.body.isNotEmpty
          ? jsonDecode(response.body) as Map<String, dynamic>
          : null;
      throw Exception(body?['error'] ?? 'Rezervaci se nepodařilo uložit.');
    }

    await fetchReservations(forceRefresh: true);
  }

  Future<List<Map<String, dynamic>>> fetchReservations({
    bool forceRefresh = false,
  }) async {
    if (!forceRefresh && _reservationsLoaded) {
      return getMyReservations();
    }

    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');

    if (userId == null) {
      _reservations = [];
      _reservationsLoaded = true;
      return getMyReservations();
    }

    final response = await http.get(
      ApiConfig.uri('/api/reservations', query: {'user_id': userId}),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Nepodařilo se načíst rezervace (kód ${response.statusCode}).',
      );
    }

    final List<dynamic> decoded = jsonDecode(response.body) as List<dynamic>;
    _reservations = decoded
        .map<Map<String, dynamic>>(
          (item) => Map<String, dynamic>.from(item as Map),
        )
        .toList();
    _reservationsLoaded = true;

    await prefs.setString('reservations', jsonEncode(_reservations));
    return getMyReservations();
  }

  Future<void> _loadReservations() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      await fetchReservations(forceRefresh: true);
      return;
    } catch (error) {
      debugPrint('Chyba při synchronizaci rezervací z API: $error');
    }

    final reservationsJson = prefs.getString('reservations');
    if (reservationsJson != null) {
      final List<dynamic> decoded =
          jsonDecode(reservationsJson) as List<dynamic>;
      _reservations = decoded
          .map<Map<String, dynamic>>(
            (item) => Map<String, dynamic>.from(item as Map),
          )
          .toList();
      _reservationsLoaded = true;
    }
  }

  void deleteRide(int id) {
    _allRides.removeWhere((ride) => ride['id'] == id);
  }

  Map<String, dynamic> _mapRide(
    Map<String, dynamic> ride,
    int? currentUserId,
  ) {
    final from = (ride['from_location']?.toString() ?? '').trim();
    final to = (ride['to_location']?.toString() ?? '').trim();
    final departure = ride['departure_time']?.toString() ?? '';

    return {
      'id': ride['id'],
      'driver_id': ride['driver_id'],
      'driver': ride['driver_name'] ?? 'Neznámý řidič',
      'driver_phone': ride['driver_phone'] ?? '+420721745084',
      'title': '${from.trim()} → ${to.trim()}',
      'from_location': from,
      'to_location': to,
      'time': _formatDateTime(departure),
      'departure_time_raw': departure,
      'seats': ride['available_seats'] ?? 0,
      'price': ride['price_per_person'] ?? ride['price'] ?? 0,
      'note': ride['description'] ?? '',
      'isMyRide': currentUserId != null && ride['driver_id'] == currentUserId,
    };
  }

  String _formatDateTime(String value) {
    if (value.isEmpty) return '';
    final normalized =
        value.contains('T') ? value : value.replaceFirst(' ', 'T');
    try {
      final dt = DateTime.parse(normalized);
      final two = (int v) => v.toString().padLeft(2, '0');
      return '${two(dt.day)}.${two(dt.month)}.${dt.year} '
          '${two(dt.hour)}:${two(dt.minute)}';
    } catch (_) {
      return value;
    }
  }
}
