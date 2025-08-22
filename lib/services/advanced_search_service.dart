import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';

class SearchResult {
  final String id;
  final String text;
  final String? subtitle;
  final String type;
  final String icon;
  final double? distance;
  final double confidence;
  final Map<String, dynamic>? data;

  SearchResult({
    required this.id,
    required this.text,
    this.subtitle,
    required this.type,
    required this.icon,
    this.distance,
    required this.confidence,
    this.data,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      id: json['id'],
      text: json['text'],
      subtitle: json['subtitle'],
      type: json['type'],
      icon: json['icon'],
      distance: json['distance']?.toDouble(),
      confidence: json['confidence']?.toDouble() ?? 0.0,
      data: json['data'],
    );
  }
}

class AdvancedSearchService {
  static final AdvancedSearchService _instance = AdvancedSearchService._internal();
  factory AdvancedSearchService() => _instance;
  AdvancedSearchService._internal();

  final Map<String, List<SearchResult>> _searchCache = {};
  List<SearchResult> _searchHistory = [];
  List<SearchResult> _popularDestinations = [];
  Timer? _debounceTimer;
  int _currentSearchId = 0;

  Future<void> initialize() async {
    await _loadPopularDestinations();
  }

  Future<void> _loadPopularDestinations() async {
    _popularDestinations = [
      SearchResult(
        id: 'praha',
        text: 'Praha',
        type: 'popular',
        icon: '🏛️',
        confidence: 1.0,
      ),
      SearchResult(
        id: 'brno',
        text: 'Brno',
        type: 'popular',
        icon: '🏙️',
        confidence: 1.0,
      ),
      SearchResult(
        id: 'ostrava',
        text: 'Ostrava',
        type: 'popular',
        icon: '🏭',
        confidence: 1.0,
      ),
    ];
  }

  Future<List<SearchResult>> search(String query, {
    bool includeRides = true,
    bool includeUsers = true,
    bool includePlaces = true,
    int debounceMs = 300,
  }) async {
    final searchId = ++_currentSearchId;
    
    _debounceTimer?.cancel();
    final completer = Completer<List<SearchResult>>();
    
    _debounceTimer = Timer(Duration(milliseconds: debounceMs), () async {
      if (searchId != _currentSearchId) {
        completer.complete([]);
        return;
      }
      
      try {
        final results = await _performSearch(query, 
          includeRides: includeRides,
          includeUsers: includeUsers,
          includePlaces: includePlaces,
        );
        completer.complete(results);
      } catch (error) {
        completer.completeError(error);
      }
    });
    
    return completer.future;
  }

  Future<List<SearchResult>> _performSearch(String query, {
    required bool includeRides,
    required bool includeUsers,
    required bool includePlaces,
  }) async {
    final trimmedQuery = query.trim();
    
    if (trimmedQuery.length < 2) {
      return _getSuggestions();
    }

    final cacheKey = trimmedQuery;
    if (_searchCache.containsKey(cacheKey)) {
      return _searchCache[cacheKey]!;
    }

    final List<Future<List<SearchResult>>> searches = [];

    if (includePlaces) {
      searches.add(_searchPlaces(trimmedQuery));
    }

    if (includeRides) {
      searches.add(_searchRides(trimmedQuery));
    }

    if (includeUsers) {
      searches.add(_searchUsers(trimmedQuery));
    }

    searches.add(Future.value(_searchInHistory(trimmedQuery)));

    final results = await Future.wait(searches);
    final mergedResults = _mergeAndRankResults(results.expand((x) => x).toList(), trimmedQuery);

    _searchCache[cacheKey] = mergedResults;

    return mergedResults;
  }

  Future<List<SearchResult>> _searchPlaces(String query) async {
    final czechCities = [
      'Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Ústí nad Labem',
      'České Budějovice', 'Hradec Králové', 'Pardubice', 'Zlín', 'Havířov',
      'Kladno', 'Most', 'Opava', 'Frýdek-Místek', 'Karviná', 'Jihlava'
    ];

    return czechCities
        .where((city) => _fuzzyMatch(query, city))
        .map((city) => SearchResult(
              id: city.toLowerCase(),
              text: city,
              type: 'place',
              icon: '🏙️',
              confidence: _calculateTextConfidence(query, city),
            ))
        .toList();
  }

  Future<List<SearchResult>> _searchRides(String query) async {
    return [];
  }

  Future<List<SearchResult>> _searchUsers(String query) async {
    try {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final mockUsers = [
        {
          'id': 1,
          'name': 'Jan Novák',
          'phone': '+420123456789',
          'rating': 4.8,
        },
        {
          'id': 2,
          'name': 'Marie Svobodová',
          'phone': '+420987654321',
          'rating': 4.9,
        },
      ];

      return mockUsers
          .where((user) => _fuzzyMatch(query, user['name'] as String))
          .map((user) => SearchResult(
                id: 'user_${user['id']}',
                text: user['name'] as String,
                subtitle: '⭐ ${(user['rating'] as double).toStringAsFixed(1)} • ${user['phone']}',
                type: 'user',
                icon: '👤',
                confidence: _calculateTextConfidence(query, user['name'] as String),
                data: user,
              ))
          .toList();
    } catch (error) {
      debugPrint('Chyba při hledání uživatelů: $error');
      return [];
    }
  }

  List<SearchResult> _searchInHistory(String query) {
    return _searchHistory
        .where((item) => _fuzzyMatch(query, item.text))
        .map((item) => SearchResult(
              id: item.id,
              text: item.text,
              subtitle: item.subtitle,
              type: 'history',
              icon: '🕒',
              confidence: _calculateTextConfidence(query, item.text),
            ))
        .toList();
  }

  List<SearchResult> _getSuggestions() {
    final suggestions = <SearchResult>[];

    suggestions.addAll(_searchHistory.take(3));
    suggestions.addAll(_popularDestinations.take(3));

    suggestions.add(SearchResult(
      id: 'current_location',
      text: 'Moje poloha',
      type: 'location',
      icon: '📍',
      confidence: 1.0,
    ));

    return suggestions;
  }

  bool _fuzzyMatch(String query, String text, {double threshold = 0.6}) {
    final similarity = _calculateSimilarity(query.toLowerCase(), text.toLowerCase());
    return similarity >= threshold;
  }

  double _calculateSimilarity(String str1, String str2) {
    if (str1.isEmpty) return str2.isEmpty ? 1.0 : 0.0;
    if (str2.isEmpty) return 0.0;

    final matrix = List.generate(
      str2.length + 1,
      (i) => List.generate(str1.length + 1, (j) => 0),
    );

    for (int i = 0; i <= str2.length; i++) {
      matrix[i][0] = i;
    }

    for (int j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (int i = 1; i <= str2.length; i++) {
      for (int j = 1; j <= str1.length; j++) {
        if (str2[i - 1] == str1[j - 1]) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = [
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1,
          ].reduce(min);
        }
      }
    }

    final maxLen = max(str1.length, str2.length);
    return maxLen == 0 ? 1.0 : (maxLen - matrix[str2.length][str1.length]) / maxLen;
  }

  double _calculateTextConfidence(String query, String text) {
    final similarity = _calculateSimilarity(query.toLowerCase(), text.toLowerCase());
    final startsWithBonus = text.toLowerCase().startsWith(query.toLowerCase()) ? 0.2 : 0.0;
    final containsBonus = text.toLowerCase().contains(query.toLowerCase()) ? 0.1 : 0.0;
    
    return (similarity + startsWithBonus + containsBonus).clamp(0.0, 1.0);
  }

  List<SearchResult> _mergeAndRankResults(List<SearchResult> results, String query) {
    final uniqueResults = <String, SearchResult>{};
    for (final result in results) {
      if (!uniqueResults.containsKey(result.id) || 
          uniqueResults[result.id]!.confidence < result.confidence) {
        uniqueResults[result.id] = result;
      }
    }

    final sortedResults = uniqueResults.values.toList();

    sortedResults.sort((a, b) {
      const typeOrder = {'history': 0, 'place': 1, 'ride': 2, 'user': 3};
      final typeDiff = (typeOrder[a.type] ?? 99) - (typeOrder[b.type] ?? 99);
      
      if (typeDiff != 0) return typeDiff;
      
      return b.confidence.compareTo(a.confidence);
    });

    return sortedResults.take(10).toList();
  }

  Future<void> selectResult(SearchResult result) async {
    await _addToHistory(result);
  }

  Future<void> _addToHistory(SearchResult result) async {
    _searchHistory.removeWhere((item) => item.id == result.id);
    _searchHistory.insert(0, result);
    
    if (_searchHistory.length > 20) {
      _searchHistory = _searchHistory.take(20).toList();
    }
  }

  void clearCache() {
    _searchCache.clear();
  }

  Future<void> clearHistory() async {
    _searchHistory.clear();
  }
}