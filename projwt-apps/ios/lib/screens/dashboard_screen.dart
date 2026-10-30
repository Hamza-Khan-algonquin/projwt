import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';
import 'gesture_demo_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => context.read<ProjWTProvider>().refreshState(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Status Card
              _buildStatusCard(context, provider),
              const SizedBox(height: 24),

              // Quick Actions (Arm/Panic)
              _buildQuickActions(context, provider),
              const SizedBox(height: 16),

              // Gesture Tutorial Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const GestureDemoScreen(),
                    ),
                  ),
                  icon: const Icon(Icons.school),
                  label: const Text('Learn Gestures'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    backgroundColor: Colors.purple,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Command Grid
              if (provider.commands.isNotEmpty)
                _buildCommandGrid(context, provider),

              // Last Command Result
              if (provider.lastCommandResult != null) ...[
                const SizedBox(height: 16),
                _buildResultCard(provider.lastCommandResult!),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusCard(BuildContext context, ProjWTProvider provider) {
    final isArmed = provider.currentState != 'IDLE';
    final statusColor = isArmed ? Colors.orange : Colors.green;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Vehicle Status',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  width: 16,
                  height: 16,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: statusColor,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        provider.currentState,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      Text(
                        isArmed ? 'Ready for commands' : 'Disarmed',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context, ProjWTProvider provider) {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: provider.isLoading ? null : () => provider.arm(),
            icon: const Icon(Icons.lock_outline),
            label: const Text('ARM'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
              backgroundColor: Colors.blue,
              foregroundColor: Colors.white,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: provider.isLoading ? null : () => provider.panic(),
            icon: const Icon(Icons.warning),
            label: const Text('PANIC'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCommandGrid(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Commands',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.2,
          ),
          itemCount: provider.commands.length,
          itemBuilder: (context, index) {
            final command = provider.commands[index];
            return _buildCommandButton(context, provider, command);
          },
        ),
      ],
    );
  }

  Widget _buildCommandButton(
    BuildContext context,
    ProjWTProvider provider,
    String command,
  ) {
    final icon = _getCommandIcon(command);
    final color = _getCommandColor(command);

    return Material(
      child: InkWell(
        onTap: provider.isLoading ? null : () => provider.sendCommand(command),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            border: Border.all(color: color.withOpacity(0.3)),
            borderRadius: BorderRadius.circular(12),
            color: color.withOpacity(0.1),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: 8),
              Text(
                command.replaceAll('_', ' ').toUpperCase(),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultCard(String result) {
    return Card(
      color: Colors.green.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            const Icon(Icons.check_circle, color: Colors.green),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                result,
                style: const TextStyle(color: Colors.green),
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getCommandIcon(String command) {
    switch (command) {
      case 'unlock':
        return Icons.lock_open;
      case 'lock':
        return Icons.lock;
      case 'flash':
        return Icons.lightbulb;
      case 'honk':
        return Icons.volume_up;
      case 'frunk':
        return Icons.door_front;
      case 'climate_warm':
      case 'climate_cool':
      case 'climate_on':
        return Icons.thermostat;
      case 'charge_port_open':
        return Icons.power;
      default:
        return Icons.check_circle;
    }
  }

  Color _getCommandColor(String command) {
    switch (command) {
      case 'unlock':
        return Colors.green;
      case 'lock':
        return Colors.red;
      case 'flash':
        return Colors.amber;
      case 'honk':
        return Colors.blue;
      default:
        return Colors.purple;
    }
  }
}
