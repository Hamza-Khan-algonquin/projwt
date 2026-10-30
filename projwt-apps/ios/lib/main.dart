import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import 'providers/projwt_provider.dart';
import 'screens/dashboard_screen.dart';
import 'screens/advanced_fitness_screen.dart';
import 'screens/gestures_screen.dart';
import 'screens/summon_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ProjWTProvider()..initialize(),
        ),
      ],
      child: const ProjWTApp(),
    ),
  );
}

class ProjWTApp extends StatelessWidget {
  const ProjWTApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ProjWT',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0066CC),
          brightness: Brightness.light,
        ),
        textTheme: GoogleFonts.robotoTextTheme(),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0066CC),
          brightness: Brightness.dark,
        ),
        textTheme: GoogleFonts.robotoTextTheme(
          ThemeData(brightness: Brightness.dark).textTheme,
        ),
      ),
      themeMode: ThemeMode.system,
      home: const MainNavigation(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({Key? key}) : super(key: key);

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const DashboardScreen(),
    const AdvancedFitnessScreen(),
    const GesturesScreen(),
    const SummonScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ProjWT'),
        subtitle: Consumer<ProjWTProvider>(
          builder: (context, provider, _) {
            final status = provider.isConnected
                ? 'Connected • ${provider.currentState}'
                : 'Offline';
            return Text(
              status,
              style: Theme.of(context).textTheme.labelSmall,
            );
          },
        ),
        elevation: 0,
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (int index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.directions_car),
            label: 'Control',
          ),
          NavigationDestination(
            icon: Icon(Icons.favorite),
            label: 'Fitness',
          ),
          NavigationDestination(
            icon: Icon(Icons.gesture),
            label: 'Gestures',
          ),
          NavigationDestination(
            icon: Icon(Icons.play_circle),
            label: 'Summon',
          ),
        ],
      ),
    );
  }
}
