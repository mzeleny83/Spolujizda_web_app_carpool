import 'package:flutter/material.dart';
import '../services/advanced_search_service.dart';

class FindRideScreen extends StatefulWidget {
  const FindRideScreen({super.key});

  @override
  State<FindRideScreen> createState() => _FindRideScreenState();
}

class _FindRideScreenState extends State<FindRideScreen> {
  final _fromController = TextEditingController();
  final _toController = TextEditingController();
  final _timeController = TextEditingController();
  final _searchService = AdvancedSearchService();
  
  List<SearchResult> _fromResults = [];
  List<SearchResult> _toResults = [];
  bool _showFromResults = false;
  bool _showToResults = false;
  final FocusNode _fromFocus = FocusNode();
  final FocusNode _toFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    _searchService.initialize();
    
    _fromController.addListener(() {
      if (_fromController.text.isNotEmpty) {
        _performSearch(_fromController.text, true);
      } else {
        setState(() {
          _fromResults = [];
          _showFromResults = false;
        });
      }
    });
    
    _toController.addListener(() {
      if (_toController.text.isNotEmpty) {
        _performSearch(_toController.text, false);
      } else {
        setState(() {
          _toResults = [];
          _showToResults = false;
        });
      }
    });
    
    _fromFocus.addListener(() {
      setState(() {
        _showFromResults = _fromFocus.hasFocus && _fromResults.isNotEmpty;
      });
    });
    
    _toFocus.addListener(() {
      setState(() {
        _showToResults = _toFocus.hasFocus && _toResults.isNotEmpty;
      });
    });
  }

  void _performSearch(String query, bool isFrom) async {
    try {
      final results = await _searchService.search(
        query,
        includePlaces: true,
        includeRides: false,
        includeUsers: false,
      );
      
      setState(() {
        if (isFrom) {
          _fromResults = results;
          _showFromResults = _fromFocus.hasFocus && results.isNotEmpty;
        } else {
          _toResults = results;
          _showToResults = _toFocus.hasFocus && results.isNotEmpty;
        }
      });
    } catch (error) {
      debugPrint('Chyba při vyhledávání: $error');
    }
  }

  void _selectResult(SearchResult result, bool isFrom) {
    setState(() {
      if (isFrom) {
        _fromController.text = result.text;
        _showFromResults = false;
        _fromFocus.unfocus();
      } else {
        _toController.text = result.text;
        _showToResults = false;
        _toFocus.unfocus();
      }
    });
    
    _searchService.selectResult(result);
  }

  Widget _buildSearchResults(List<SearchResult> results, bool isFrom) {
    if (results.isEmpty) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.only(top: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: results.length,
        separatorBuilder: (context, index) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final result = results[index];
          return ListTile(
            dense: true,
            leading: Text(
              result.icon,
              style: const TextStyle(fontSize: 20),
            ),
            title: Text(
              result.text,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
            subtitle: result.subtitle != null
                ? Text(
                    result.subtitle!,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  )
                : null,
            onTap: () => _selectResult(result, isFrom),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hledat jízdu'),
        backgroundColor: Colors.blue.shade600,
        foregroundColor: Colors.white,
      ),
      body: GestureDetector(
        onTap: () {
          _fromFocus.unfocus();
          _toFocus.unfocus();
          setState(() {
            _showFromResults = false;
            _showToResults = false;
          });
        },
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextFormField(
                    controller: _fromController,
                    focusNode: _fromFocus,
                    decoration: InputDecoration(
                      labelText: 'Odkud',
                      hintText: 'Zadejte výchozí místo',
                      border: const OutlineInputBorder(),
                      prefixIcon: const Icon(Icons.location_on, color: Colors.green),
                      suffixIcon: _fromController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                _fromController.clear();
                                setState(() {
                                  _fromResults = [];
                                  _showFromResults = false;
                                });
                              },
                            )
                          : null,
                    ),
                  ),
                  if (_showFromResults) _buildSearchResults(_fromResults, true),
                ],
              ),
              const SizedBox(height: 16),
              
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextFormField(
                    controller: _toController,
                    focusNode: _toFocus,
                    decoration: InputDecoration(
                      labelText: 'Kam',
                      hintText: 'Zadejte cílové místo',
                      border: const OutlineInputBorder(),
                      prefixIcon: const Icon(Icons.flag, color: Colors.red),
                      suffixIcon: _toController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                _toController.clear();
                                setState(() {
                                  _toResults = [];
                                  _showToResults = false;
                                });
                              },
                            )
                          : null,
                    ),
                  ),
                  if (_showToResults) _buildSearchResults(_toResults, false),
                ],
              ),
              const SizedBox(height: 16),
              
              TextFormField(
                controller: _timeController,
                decoration: const InputDecoration(
                  labelText: 'Čas odjezdu',
                  hintText: 'Vyberte čas',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.access_time, color: Colors.blue),
                ),
                readOnly: true,
                onTap: () async {
                  final time = await showTimePicker(
                    context: context,
                    initialTime: TimeOfDay.now(),
                  );
                  if (time != null) {
                    _timeController.text = time.format(context);
                  }
                },
              ),
              const SizedBox(height: 32),
              
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: _fromController.text.isNotEmpty && _toController.text.isNotEmpty
                      ? () {
                          Navigator.pushNamed(context, '/matches', arguments: {
                            'from': _fromController.text,
                            'to': _toController.text,
                            'time': _timeController.text,
                          });
                        }
                      : null,
                  icon: const Icon(Icons.search),
                  label: const Text(
                    'Hledat jízdy',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade600,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _fromController.dispose();
    _toController.dispose();
    _timeController.dispose();
    _fromFocus.dispose();
    _toFocus.dispose();
    super.dispose();
  }
}