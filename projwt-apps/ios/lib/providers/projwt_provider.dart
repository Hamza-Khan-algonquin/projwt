import 'package:flutter/material.dart';
import '../services/api_client.dart';

class ProjWTProvider extends ChangeNotifier {
  final ProjWTAPIClient api = ProjWTAPIClient();

  String _currentState = 'IDLE';
  List<String> _commands = [];
  bool _isConnected = false;
  bool _isLoading = false;

  // Biometrics
  int _heartRate = 0;
  int _battery = 100;
  final List<int> _historicalHeartRate = [];

  // Gestures
  bool _isBandConnected = false;
  String? _bandAddress;
  int _bandSignalStrength = 0;
  String? _lastGestureTime;
  final List<Map<String, String>> _gestureHistory = [];

  // Advanced Fitness Metrics
  int _recoveryScore = 78;
  double _strainScore = 8.5;
  int _sleepScore = 85;
  String _stressLevel = 'Low';
  int _restingHeartRate = 52;
  int _hrv = 68;
  int _maxHeartRate = 168;
  int _sleepDuration = 7;
  int _sleepMinutes = 32;

  // Results
  String? _lastCommandResult;

  // Getters - Basic
  String get currentState => _currentState;
  List<String> get commands => _commands;
  bool get isConnected => _isConnected;
  bool get isLoading => _isLoading;
  int get heartRate => _heartRate;
  int get battery => _battery;
  String? get lastCommandResult => _lastCommandResult;

  // Getters - Fitness
  List<int> getHistoricalHeartRate() {
    if (_historicalHeartRate.isEmpty) {
      return [72, 75, 78, 76, 80, 77, 74]; // Default 7-day data
    }
    return _historicalHeartRate.length >= 7
        ? _historicalHeartRate.sublist(_historicalHeartRate.length - 7)
        : _historicalHeartRate;
  }

  // Getters - Gestures
  bool get isBandConnected => _isBandConnected;
  String? get bandAddress => _bandAddress;
  int get bandSignalStrength => _bandSignalStrength;
  String? get lastGestureTime => _lastGestureTime;
  List<Map<String, String>> get gestureHistory => _gestureHistory;

  // Getters - Advanced Fitness
  int get recoveryScore => _recoveryScore;
  double get strainScore => _strainScore;
  int get sleepScore => _sleepScore;
  String get stressLevel => _stressLevel;
  int get restingHeartRate => _restingHeartRate;
  int get hrv => _hrv;
  int get maxHeartRate => _maxHeartRate;
  int get sleepDuration => _sleepDuration;
  int get sleepMinutes => _sleepMinutes;

  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    // Check connection
    final health = await api.getHealth();
    _isConnected = health['status'] == 'ok';

    // Load commands
    _commands = await api.getCommands();

    // Get initial state
    await refreshState();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> initializeFitnessData() async {
    // Initialize with synthetic historical data
    _historicalHeartRate.addAll([72, 75, 78, 76, 80, 77, 74]);
    notifyListeners();
  }

  Future<void> initializeGestures() async {
    // Simulate band connection
    _isBandConnected = true;
    _bandAddress = 'F0:A3:47:92:11:84';
    _bandSignalStrength = 85;
    notifyListeners();
  }

  Future<void> initializeAdvancedFitness() async {
    // Simulate daily metrics (would come from real WHOOP band)
    _recoveryScore = 78;
    _strainScore = 8.5;
    _sleepScore = 85;
    _stressLevel = 'Low';
    _restingHeartRate = 52;
    _hrv = 68;
    _maxHeartRate = 168;
    _sleepDuration = 7;
    _sleepMinutes = 32;
    notifyListeners();
  }

  Future<void> refreshState() async {
    final state = await api.getState();
    if (state.containsKey('state')) {
      _currentState = state['state'];
      notifyListeners();
    }
  }

  Future<void> sendCommand(String command) async {
    _isLoading = true;
    _lastCommandResult = 'Sending $command...';
    notifyListeners();

    final result = await api.sendCommand(command);
    _lastCommandResult = result['ok'] ? 'Command sent!' : result['error'];

    if (result.containsKey('state')) {
      _currentState = result['state'];
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> arm() async {
    _isLoading = true;
    notifyListeners();

    final result = await api.armGesture();
    _currentState = result['state'] ?? 'ARMED';

    _isLoading = false;
    notifyListeners();
  }

  Future<void> panic() async {
    _isLoading = true;
    notifyListeners();

    final result = await api.panicGesture();
    _currentState = result['state'] ?? 'IDLE';

    _isLoading = false;
    notifyListeners();
  }

  Stream<Map<String, dynamic>> getBiometricsStream() {
    return api.streamBiometrics().map((data) {
      if (!data.containsKey('error')) {
        _heartRate = data['heart_rate'] ?? 0;
        _battery = data['battery'] ?? 100;

        // Keep historical data (max 1000 points)
        _historicalHeartRate.add(_heartRate);
        if (_historicalHeartRate.length > 1000) {
          _historicalHeartRate.removeAt(0);
        }
      }
      return data;
    });
  }

  void recordGesture(String gesture) {
    final now = DateTime.now();
    final timeString = '${now.hour}:${now.minute.toString().padLeft(2, '0')}';

    _gestureHistory.insert(0, {
      'gesture': gesture.replaceAll('_', ' ').toUpperCase(),
      'time': timeString,
    });

    _lastGestureTime = timeString;

    // Keep only last 20 gestures
    if (_gestureHistory.length > 20) {
      _gestureHistory.removeLast();
    }

    notifyListeners();
  }

  void clearGestureHistory() {
    _gestureHistory.clear();
    notifyListeners();
  }

  void connectWHOOPBand({
    required String name,
    required String address,
    required int signalStrength,
  }) {
    _isBandConnected = true;
    _bandAddress = address;
    _bandSignalStrength = signalStrength;
    notifyListeners();
  }

  void disconnectWHOOPBand() {
    _isBandConnected = false;
    _bandAddress = null;
    _bandSignalStrength = 0;
    notifyListeners();
  }

  void updateMetrics({
    int? recovery,
    double? strain,
    int? sleepScore,
    String? stress,
    int? rhr,
    int? hrvValue,
    int? maxHR,
  }) {
    if (recovery != null) _recoveryScore = recovery;
    if (strain != null) _strainScore = strain;
    if (sleepScore != null) _sleepScore = sleepScore;
    if (stress != null) _stressLevel = stress;
    if (rhr != null) _restingHeartRate = rhr;
    if (hrvValue != null) _hrv = hrvValue;
    if (maxHR != null) _maxHeartRate = maxHR;
    notifyListeners();
  }

  @override
  void dispose() {
    api.closeBiometricStream();
    super.dispose();
  }
}
