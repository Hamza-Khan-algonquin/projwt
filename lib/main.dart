import 'package:flutter/material.dart';

void main() {
  runApp(const ProjWTApp());
}

class ProjWTApp extends StatelessWidget {
  const ProjWTApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ProjWT - Tesla Control',
      theme: _buildDarkTheme(),
      home: const MainNavigationScreen(),
      debugShowCheckedModeBanner: false,
    );
  }

  static ThemeData _buildDarkTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF0A0E27),
      colorScheme: ColorScheme.dark(
        background: const Color(0xFF0A0E27),
        surface: const Color(0xFF1A1F3A),
        surfaceVariant: const Color(0xFF2A3150),
        onBackground: const Color(0xFFE0E0E0),
        onSurface: const Color(0xFFE0E0E0),
        primary: const Color(0xFF00D9FF),
        onPrimary: const Color(0xFF000000),
        secondary: const Color(0xFFB84FFF),
        onSecondary: const Color(0xFF000000),
        tertiary: const Color(0xFF00FF88),
        onTertiary: const Color(0xFF000000),
        error: const Color(0xFFFF6B6B),
        onError: const Color(0xFF000000),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Color(0xFFE0E0E0)),
        headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFFE0E0E0)),
        headlineSmall: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFFE0E0E0)),
        bodyLarge: TextStyle(fontSize: 16, color: Color(0xFFE0E0E0)),
        bodyMedium: TextStyle(fontSize: 14, color: Color(0xFFA0A0A0)),
        labelSmall: TextStyle(fontSize: 12, color: Color(0xFF808080)),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF1A1F3A),
        foregroundColor: Color(0xFFE0E0E0),
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFF1A1F3A),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: Color(0xFF2A3150), width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF00D9FF),
          foregroundColor: const Color(0xFF000000),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({Key? key}) : super(key: key);

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;
  final List<Widget> _screens = [
    const DashboardScreen(),
    const FitnessScreen(),
    const GesturesScreen(),
    const SummonScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (int index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.directions_car), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.favorite), label: 'Fitness'),
          NavigationDestination(icon: Icon(Icons.touch_app), label: 'Gestures'),
          NavigationDestination(icon: Icon(Icons.location_on), label: 'Summon'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}

// DASHBOARD SCREEN
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tesla Control')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Vehicle Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildStatusItem('🔒 Locked', const Color(0xFF00FF88)),
                          _buildStatusItem('🔋 82%', const Color(0xFF00D9FF)),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text('Controls', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                children: [
                  _buildControlButton('🔓 Unlock', 0xFF00D9FF),
                  _buildControlButton('🔒 Lock', 0xFFB84FFF),
                  _buildControlButton('📢 Honk', 0xFF00FF88),
                  _buildControlButton('💡 Flash', 0xFFFFB800),
                  _buildControlButton('❄️ Climate', 0xFF00D9FF),
                  _buildControlButton('⚡ Charge', 0xFF00FF88),
                ],
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.stop_circle),
                  label: const Text('🛑 PANIC STOP'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFF6B6B),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusItem(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
    );
  }

  Widget _buildControlButton(String label, int colorValue) {
    return Card(
      child: InkWell(
        onTap: () {},
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Color(colorValue), width: 2),
          ),
          child: Center(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(colorValue)),
            ),
          ),
        ),
      ),
    );
  }
}

// FITNESS SCREEN
class FitnessScreen extends StatelessWidget {
  const FitnessScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fitness & Biometrics')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Text('Recovery Score', style: TextStyle(fontSize: 14, color: Color(0xFFA0A0A0))),
                      const SizedBox(height: 8),
                      const Text('72%', style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Color(0xFF00FF88))),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: 0.72,
                        backgroundColor: const Color(0xFF2A3150),
                        valueColor: AlwaysStoppedAnimation(const Color(0xFF00FF88).withOpacity(0.7)),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text('Key Metrics', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                children: [
                  _buildMetricCard('❤️ HR', '68 bpm', const Color(0xFFFF6B6B)),
                  _buildMetricCard('⚡ Strain', '4.2', const Color(0xFFB84FFF)),
                  _buildMetricCard('😴 Sleep', '7h 32m', const Color(0xFF00D9FF)),
                  _buildMetricCard('🔋 Battery', '62%', const Color(0xFFFFB800)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFFA0A0A0))),
            const SizedBox(height: 8),
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
          ],
        ),
      ),
    );
  }
}

// GESTURES SCREEN
class GesturesScreen extends StatelessWidget {
  const GesturesScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gesture Control')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('WHOOP Band', style: TextStyle(fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('Connected', style: TextStyle(fontSize: 12, color: Color(0xFFA0A0A0))),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00FF88).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF00FF88), width: 1),
                        ),
                        child: const Text('✓ On Wrist', style: TextStyle(color: Color(0xFF00FF88), fontSize: 12, fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text('Gesture Vocabulary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildGestureItem('🔓 Unlock', 'tap → double_tap → tap'),
              _buildGestureItem('🔒 Lock', 'double_tap → tap'),
              _buildGestureItem('📢 Honk', 'dwell (hold 2 sec)'),
              _buildGestureItem('🛑 Panic', 'shake vigorously'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGestureItem(String action, String gesture) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(action, style: const TextStyle(fontWeight: FontWeight.w600)),
            Text(gesture, style: const TextStyle(fontSize: 12, color: Color(0xFFA0A0A0), fontFamily: 'monospace')),
          ],
        ),
      ),
    );
  }
}

// SUMMON SCREEN
class SummonScreen extends StatelessWidget {
  const SummonScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Summon (Auto Move)')),
      body: SafeArea(
        child: Center(
          child: Card(
            margin: const EdgeInsets.all(16),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.location_on, size: 64, color: Color(0xFF00D9FF)),
                  const SizedBox(height: 16),
                  const Text('Autonomous Movement', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('Coming Soon', style: TextStyle(color: Color(0xFFA0A0A0))),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {},
                      child: const Text('Start Summon'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// SETTINGS SCREEN
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _whoopControlEnabled = false;
  final TextEditingController _teslaTokenController = TextEditingController();
  final TextEditingController _teslaVinController = TextEditingController();
  bool _teslaSaved = false;
  bool _whoopConnected = false;
  bool _showTeslaForm = false;

  @override
  void dispose() {
    _teslaTokenController.dispose();
    _teslaVinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Tesla API', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('API Credentials', style: TextStyle(fontWeight: FontWeight.w600)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: _teslaSaved ? const Color(0xFF00FF88).withOpacity(0.2) : const Color(0xFFFF6B6B).withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _teslaSaved ? '✓ Saved' : '✗ Not Set',
                              style: TextStyle(
                                color: _teslaSaved ? const Color(0xFF00FF88) : const Color(0xFFFF6B6B),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (_showTeslaForm) ...[
                        const SizedBox(height: 16),
                        TextField(
                          controller: _teslaTokenController,
                          decoration: InputDecoration(
                            labelText: 'API Token',
                            hintText: 'Your Tesla API token',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          obscureText: true,
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _teslaVinController,
                          decoration: InputDecoration(
                            labelText: 'Vehicle VIN',
                            hintText: 'Your Tesla VIN',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: () {
                              if (_teslaTokenController.text.isNotEmpty && _teslaVinController.text.isNotEmpty) {
                                setState(() {
                                  _teslaSaved = true;
                                  _showTeslaForm = false;
                                });
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Tesla credentials saved!'), backgroundColor: Color(0xFF00FF88)),
                                );
                              }
                            },
                            child: const Text('Save Credentials'),
                          ),
                        ),
                      ] else ...[
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: () {
                              setState(() {
                                _showTeslaForm = true;
                              });
                            },
                            child: const Text('Enter Credentials'),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text('WHOOP Band', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Connection Status', style: TextStyle(fontWeight: FontWeight.w600)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: _whoopConnected ? const Color(0xFF00FF88).withOpacity(0.2) : const Color(0xFFFF6B6B).withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _whoopConnected ? '✓ Connected' : '✗ Not Connected',
                              style: TextStyle(
                                color: _whoopConnected ? const Color(0xFF00FF88) : const Color(0xFFFF6B6B),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            setState(() {
                              _whoopConnected = !_whoopConnected;
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(_whoopConnected ? 'Scanning for WHOOP band...' : 'Disconnected from WHOOP')),
                            );
                          },
                          icon: Icon(_whoopConnected ? Icons.bluetooth_connected : Icons.bluetooth),
                          label: Text(_whoopConnected ? 'Disconnect' : 'Connect Band'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Enable WHOOP Control', style: TextStyle(fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('Use band for Tesla commands', style: TextStyle(fontSize: 12, color: Color(0xFFA0A0A0))),
                        ],
                      ),
                      Switch(
                        value: _whoopControlEnabled,
                        activeColor: const Color(0xFF00D9FF),
                        onChanged: (value) {
                          setState(() {
                            _whoopControlEnabled = value;
                          });
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
