import React, { useEffect, useState } from 'react';
import { Alert, Modal, Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type { AlertButton } from 'react-native';
import { Colors } from '../../constants/colors';
import { FontSize, Radius, Spacing } from '../../constants/theme';

/**
 * react-native-web ships Alert.alert as a no-op, so confirmations (delete, log out) and info
 * dialogs never appeared in the web build. On web, route Alert.alert to this in-app dialog.
 */
type Dialog = { title: string; message?: string; buttons: AlertButton[] };

let show: ((d: Dialog) => void) | null = null;

if (Platform.OS === 'web') {
  Alert.alert = (title, message, buttons) => {
    show?.({ title, message, buttons: buttons && buttons.length ? buttons : [{ text: 'OK' }] });
  };
}

export default function WebAlertHost() {
  const [dialog, setDialog] = useState<Dialog | null>(null);

  useEffect(() => {
    if (Platform.OS !== 'web') return;
    show = setDialog;
    return () => {
      show = null;
    };
  }, []);

  if (!dialog) return null;

  const press = (b: AlertButton) => {
    setDialog(null);
    b.onPress?.();
  };

  return (
    <Modal transparent visible animationType="fade" onRequestClose={() => setDialog(null)}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>{dialog.title}</Text>
          {!!dialog.message && <Text style={styles.message}>{dialog.message}</Text>}
          <View style={styles.buttons}>
            {dialog.buttons.map((b, i) => (
              <TouchableOpacity
                key={`${b.text}-${i}`}
                style={[
                  styles.button,
                  b.style === 'cancel' && styles.cancel,
                  b.style === 'destructive' && styles.destructive,
                ]}
                onPress={() => press(b)}
                activeOpacity={0.8}
              >
                <Text
                  style={[
                    styles.buttonText,
                    b.style === 'cancel' && styles.cancelText,
                  ]}
                >
                  {b.text ?? 'OK'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  card: {
    width: '100%',
    maxWidth: 340,
    backgroundColor: Colors.darkCard,
    borderRadius: Radius.cardLg,
    padding: Spacing.lg,
    borderWidth: 1,
    borderColor: Colors.borderDark,
  },
  title: {
    fontFamily: 'Poppins_600SemiBold',
    fontSize: FontSize.lg,
    color: Colors.textPrimaryDark,
    marginBottom: Spacing.xs,
  },
  message: {
    fontFamily: 'Poppins_400Regular',
    fontSize: FontSize.base,
    color: Colors.textSecondary,
    lineHeight: 21,
  },
  buttons: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.lg },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: Radius.pill,
    backgroundColor: Colors.accentStart,
    alignItems: 'center',
  },
  cancel: { backgroundColor: Colors.darkCardAlt },
  destructive: { backgroundColor: Colors.expense },
  buttonText: { fontFamily: 'Poppins_600SemiBold', fontSize: FontSize.base, color: '#fff' },
  cancelText: { color: Colors.textSecondary },
});
