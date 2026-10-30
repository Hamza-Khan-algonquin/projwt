import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class GestureDemoScreen extends StatefulWidget {
  const GestureDemoScreen({Key? key}) : super(key: key);

  @override
  State<GestureDemoScreen> createState() => _GestureDemoScreenState();
}

class _GestureDemoScreenState extends State<GestureDemoScreen>
    with TickerProviderStateMixin {
  late TabController _tabController;
  String? _lastDetectedGesture;
  String? _executedCommand;

  final Map<String, GestureInfo> gestureMap = {
    'tap': GestureInfo(
      name: 'Single Tap',
      description: 'Cycle to next command in menu',
      icon: Icons.touch_app,
      color: Colors.blue,
      command: null, // No direct command, cycles menu
      visual: '👆',
      demo: 'Tap and hold on your wrist for ~500ms',
    ),
    'double_tap': GestureInfo(
      name: 'Double Tap',
      description: 'ARM the system (enter command mode)',
      icon: Icons.touch_app,
      color: Colors.green,
      command: 'arm',
      visual: '👆👆',
      demo: 'Two quick taps, less than 1 second apart',
    ),
    'dwell': GestureInfo(
      name: 'Dwell (2.5s)',
      description: 'Confirm selected command',
      icon: Icons.timer,
      color: Colors.orange,
      command: 'confirm',
      visual: '⏱️',
      demo: 'Hold still on your wrist for 2.5 seconds',
    ),
    'shake': GestureInfo(
      name: 'Shake',
      description: 'PANIC — emergency disarm + LOCK',
      icon: Icons.warning,
      color: Colors.red,
      command: 'lock',
      visual: '🤝',
      demo: 'Vigorous wrist shake (down-up-down-up)',
    ),
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Gesture Control Tutorial'),
            elevation: 0,
          ),
          body: Column(
            children: [
              // Gesture Tabs
              TabBar(
                controller: _tabController,
                tabs: [
                  _buildGestureTab('tap', Colors.blue),
                  _buildGestureTab('double_tap', Colors.green),
                  _buildGestureTab('dwell', Colors.orange),
                  _buildGestureTab('shake', Colors.red),
                ],
              ),

              // Gesture Details
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildGestureDetail(context, 'tap', provider),
                    _buildGestureDetail(context, 'double_tap', provider),
                    _buildGestureDetail(context, 'dwell', provider),
                    _buildGestureDetail(context, 'shake', provider),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildGestureTab(String gestureKey, Color color) {
    final gesture = gestureMap[gestureKey]!;
    return Tab(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(gesture.icon, color: color),
          const SizedBox(height: 4),
          Text(
            gesture.name,
            style: const TextStyle(fontSize: 11),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildGestureDetail(
    BuildContext context,
    String gestureKey,
    ProjWTProvider provider,
  ) {
    final gesture = gestureMap[gestureKey]!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Visual Demo
          _buildVisualDemo(context, gesture),
          const SizedBox(height: 24),

          // Demo Instructions
          _buildDemoInstructions(context, gesture),
          const SizedBox(height: 24),

          // Test Button
          ElevatedButton.icon(
            onPressed: () => _testGesture(context, gestureKey, provider),
            icon: const Icon(Icons.play_circle),
            label: const Text('Test This Gesture'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
              backgroundColor: gesture.color,
              foregroundColor: Colors.white,
            ),
          ),

          const SizedBox(height: 16),

          // What Happens
          _buildWhatHappensCard(context, gesture),

          const SizedBox(height: 16),

          // Command Mapping
          _buildCommandMappingCard(context, gesture),

          const SizedBox(height: 16),

          // Real-World Tips
          _buildTipsCard(context, gesture),
        ],
      ),
    );
  }

  Widget _buildVisualDemo(BuildContext context, GestureInfo gesture) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            Text(
              gesture.visual,
              style: const TextStyle(fontSize: 64),
            ),
            const SizedBox(height: 16),
            Text(
              gesture.name,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              gesture.description,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDemoInstructions(BuildContext context, GestureInfo gesture) {
    return Card(
      color: gesture.color.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'How to Perform',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.watch, color: gesture.color, size: 24),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    gesture.demo,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWhatHappensCard(BuildContext context, GestureInfo gesture) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'What Happens',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            _buildWhatRow(
              gesture.color,
              '1',
              'WHOOP band detects motion',
            ),
            _buildWhatRow(
              gesture.color,
              '2',
              'Motion sent via Bluetooth to iPhone',
            ),
            _buildWhatRow(
              gesture.color,
              '3',
              'App recognizes gesture pattern',
            ),
            _buildWhatRow(
              gesture.color,
              '4',
              'Command sent to vehicle',
            ),
            _buildWhatRow(
              gesture.color,
              '5',
              'Car executes command instantly',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWhatRow(Color color, String number, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color,
            ),
            child: Center(
              child: Text(
                number,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }

  Widget _buildCommandMappingCard(BuildContext context, GestureInfo gesture) {
    if (gesture.command == null) {
      return Card(
        color: Colors.blue.withOpacity(0.1),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.info, color: Colors.blue),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'This gesture cycles the command menu (no direct car action)',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Car Response',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: gesture.color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: gesture.color),
              ),
              child: Text(
                gesture.command!.toUpperCase(),
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: gesture.color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTipsCard(BuildContext context, GestureInfo gesture) {
    final tips = {
      'tap': [
        'Keep your wrist flat and relaxed',
        'Use your index or middle finger',
        'Tap on the side of the band',
      ],
      'double_tap': [
        'Quick double-tap within 1 second',
        'Both taps should be firm',
        'Hold your wrist still between taps',
      ],
      'dwell': [
        'Keep tapping and hold position',
        'Count to 2-3 seconds in your head',
        'Don\'t release too early',
      ],
      'shake': [
        'Shake from wrist/forearm, not whole arm',
        '3-4 vigorous up-down motions',
        'Fast enough to feel your wrist move',
      ],
    };

    return Card(
      color: Colors.amber.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Tips & Tricks',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            ...(tips[gesture.name.toLowerCase()] ?? []).map((tip) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    const Icon(Icons.lightbulb, size: 16, color: Colors.amber),
                    const SizedBox(width: 12),
                    Expanded(child: Text(tip)),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  void _testGesture(
    BuildContext context,
    String gestureKey,
    ProjWTProvider provider,
  ) {
    final gesture = gestureMap[gestureKey]!;

    setState(() {
      _lastDetectedGesture = gesture.name;
      _executedCommand = gesture.command?.toUpperCase() ?? 'MENU CYCLE';
    });

    // Record gesture
    provider.recordGesture(gestureKey);

    // Send command if applicable
    if (gesture.command != null && gesture.command != 'confirm') {
      provider.sendCommand(gesture.command!);
    }

    // Show feedback
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('✓ Gesture Detected: ${gesture.name}'),
            if (gesture.command != null)
              Text('✓ Command Sent: ${gesture.command!.toUpperCase()}'),
          ],
        ),
        backgroundColor: gesture.color,
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

class GestureInfo {
  final String name;
  final String description;
  final IconData icon;
  final Color color;
  final String? command;
  final String visual;
  final String demo;

  GestureInfo({
    required this.name,
    required this.description,
    required this.icon,
    required this.color,
    required this.command,
    required this.visual,
    required this.demo,
  });
}
