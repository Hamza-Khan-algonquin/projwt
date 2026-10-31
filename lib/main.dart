import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'services/whoop_service.dart';
import 'services/tesla_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await StorageService().initialize();
  runApp(const ProjWTApp());
}

class ProjWTApp extends StatelessWidget {
  const ProjWTApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider(create: (_) => TeslaService()),
        Provider(create: (_) => WhoopService()),
        Provider(create: (_) => StorageService()),
      ],
      child: MaterialApp(
        title: 'ProjWT',
        theme: _buildAppleTheme(),
        home: const MainNavigationScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }

  static ThemeData _buildAppleTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF0A0E27),
      colorScheme: ColorScheme.dark(
        background: const Color(0xFF0A0E27),
        surface: const Color(0xFF1A1F3A),
        primary: const Color(0xFF00D9FF),
        secondary: const Color(0xFFB84FFF),
        tertiary: const Color(0xFF00FF88),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: Color(0xFFE0E0E0), letterSpacing: -0.5),
        headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, color: Color(0xFFE0E0E0)),
        bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Color(0xFFE0E0E0)),
        bodyMedium: TextStyle(fontSize: 14, color: Color(0xFFA0A0A0)),
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
    const ControlsScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: Colors.white.withOpacity(0.1))),
        ),
        child: NavigationBar(
          selectedIndex: _selectedIndex,
          onDestinationSelected: (int index) => setState(() => _selectedIndex = index),
          backgroundColor: const Color(0xFF1A1F3A).withOpacity(0.8),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_rounded), label: 'Home'),
            NavigationDestination(icon: Icon(Icons.favorite_rounded), label: 'Health'),
            NavigationDestination(icon: Icon(Icons.bolt_rounded), label: 'Control'),
            NavigationDestination(icon: Icon(Icons.settings_rounded), label: 'Settings'),
          ],
        ),
      ),
    );
  }
}

// DASHBOARD SCREEN
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final storage = Provider.of<StorageService>(context);
    final latest = storage.getLatestBiometric();

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Health Status', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 20),
            _AppleCard(
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _StatItem('❤️', '${latest?['heart_rate'] ?? '--'}', 'BPM'),
                      _StatItem('📈', '${latest?['recovery_score'] ?? '--'}%', 'Recovery'),
                      _StatItem('⚡', '${latest?['strain_score'] ?? '--'}', 'Strain'),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Text('Quick Control', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 16),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              children: [
                _QuickControlButton('🔓', 'Unlock', Colors.cyan),
                _QuickControlButton('🔒', 'Lock', Colors.purple),
                _QuickControlButton('📢', 'Honk', Colors.green),
                _QuickControlButton('💡', 'Flash', Colors.amber),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _StatItem(String icon, String value, String label) {
    return Column(
      children: [
        Text(icon, style: const TextStyle(fontSize: 32)),
        const SizedBox(height: 8),
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFFA0A0A0))),
      ],
    );
  }
}

// FITNESS SCREEN
class FitnessScreen extends StatelessWidget {
  const FitnessScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final storage = Provider.of<StorageService>(context);
    final latest = storage.getLatestBiometric();
    final history = storage.getBiometricHistory();

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Biometrics', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 20),
            _AppleCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Recovery Score', style: Theme.of(context).textTheme.bodyLarge),
                  const SizedBox(height: 12),
                  Text('${latest?['recovery_score'] ?? 0}%', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Color(0xFF00FF88))),
                  LinearProgressIndicator(value: (latest?['recovery_score'] ?? 0) / 100, minHeight: 8),
                ],
              ),
            ),
            const SizedBox(height: 20),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              children: [
                _MetricCard('Heart Rate', '${latest?['heart_rate'] ?? '--'} bpm', Colors.red),
                _MetricCard('Strain', '${latest?['strain_score'] ?? '--'}', Colors.orange),
                _MetricCard('Sleep', '${latest?['sleep_hours'] ?? '--'}h', Colors.blue),
                _MetricCard('Temp', '${latest?['skin_temperature'] ?? '--'}°F', Colors.cyan),
              ],
            ),
            const SizedBox(height: 24),
            if (history.length > 1)
              _AppleCard(
                child: SizedBox(
                  height: 200,
                  child: LineChart(
                    LineChartData(
                      lineBarsData: [
                        LineChartBarData(
                          spots: history.asMap().entries.map((e) {
                            return FlSpot(e.key.toDouble(), (e.value['heart_rate'] as num?)?.toDouble() ?? 0);
                          }).toList(),
                          isCurved: true,
                          color: Colors.red,
                          barWidth: 3,
                          dotData: const FlDotData(show: false),
                        ),
                      ],
                      gridData: const FlGridData(show: false),
                      borderData: FlBorderData(show: false),
                      titlesData: const FlTitlesData(show: false),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _MetricCard(String title, String value, Color color) {
    return _AppleCard(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(title, style: const TextStyle(fontSize: 12, color: Color(0xFFA0A0A0))),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }
}

// CONTROLS SCREEN
class ControlsScreen extends StatefulWidget {
  const ControlsScreen({Key? key}) : super(key: key);

  @override
  State<ControlsScreen> createState() => _ControlsScreenState();
}

class _ControlsScreenState extends State<ControlsScreen> {
  @override
  Widget build(BuildContext context) {
    final tesla = Provider.of<TeslaService>(context);

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Tesla Control', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 20),
            if (!tesla.isConfigured)
              _AppleCard(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.lock_outline_rounded, size: 32, color: Color(0xFFFF6B6B)),
                      const SizedBox(height: 12),
                      const Text('Configure Tesla credentials in Settings', textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(onPressed: () {}, child: const Text('Go to Settings')),
                    ],
                  ),
                ),
              )
            else ...[
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                children: [
                  _TeslaButton('🔓', 'Unlock', () => tesla.unlock()),
                  _TeslaButton('🔒', 'Lock', () => tesla.lock()),
                  _TeslaButton('📢', 'Honk', () => tesla.honk()),
                  _TeslaButton('💡', 'Flash', () => tesla.flashLights()),
                  _TeslaButton('❄️', 'Climate', () => tesla.setClimate(72)),
                  _TeslaButton('⚡', 'Charge', () => tesla.startCharging()),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _TeslaButton(String icon, String label, Future<bool> Function() onTap) {
    return _AppleCard(
      onTap: () async {
        final success = await onTap();
        if (success && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('$label sent!'), backgroundColor: Colors.green),
          );
        }
      },
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(icon, style: const TextStyle(fontSize: 32)),
          const SizedBox(height: 12),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
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
  late TextEditingController _tokenController;
  late TextEditingController _vinController;

  @override
  void initState() {
    super.initState();
    final storage = StorageService();
    _tokenController = TextEditingController(text: storage.getTeslaToken() ?? '');
    _vinController = TextEditingController(text: storage.getTeslaVin() ?? '');
  }

  @override
  void dispose() {
    _tokenController.dispose();
    _vinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tesla = Provider.of<TeslaService>(context);
    final storage = Provider.of<StorageService>(context);

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Settings', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 20),
            Text('Tesla Configuration', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 12),
            _AppleCard(
              child: Column(
                children: [
                  TextField(
                    controller: _tokenController,
                    decoration: InputDecoration(
                      labelText: 'API Token',
                      hintText: 'Enter your Tesla API token',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    obscureText: true,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _vinController,
                    decoration: InputDecoration(
                      labelText: 'Vehicle VIN',
                      hintText: 'Enter your vehicle VIN',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        storage.saveTeslaCredentials(_tokenController.text, _vinController.text);
                        tesla.initialize(_tokenController.text, _vinController.text);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Credentials saved!'), backgroundColor: Colors.green),
                        );
                      },
                      child: const Text('Save Credentials'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// APPLE DESIGN COMPONENTS
class _AppleCard extends StatelessWidget {
  final Widget child;
  final VoidCallback? onTap;

  const _AppleCard({required this.child, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1A1F3A).withOpacity(0.6),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: BackdropFilter(
            filter: const ui.ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: child,
            ),
          ),
        ),
      ),
    );
  }
}

class _QuickControlButton extends StatelessWidget {
  final String icon;
  final String label;
  final Color color;

  const _QuickControlButton(this.icon, this.label, this.color);

  @override
  Widget build(BuildContext context) {
    return _AppleCard(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(icon, style: const TextStyle(fontSize: 28)),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }
}

import 'dart:ui' as ui;
