class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:5000',
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
