class ApiConfig {
  /// Base URL for API calls. Override with
  /// `--dart-define API_BASE_URL=http://10.0.2.2:5000`
  /// during local development/emulator debugging.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://spolujizda-645ec54e47aa.herokuapp.com',
  );

  static Uri uri(String path, {Map<String, dynamic>? query}) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    final queryParameters = query?.map(
      (key, value) => MapEntry(key, value?.toString()),
    );
    return Uri.parse(baseUrl).replace(
      path: '${Uri.parse(baseUrl).path}$normalizedPath',
      queryParameters: queryParameters,
    );
  }
}
