from django.test import TestCase

from .compatibility import can_donate, donor_groups_for, recipient_groups_for
from .models import BloodGroup

# donor -> recipients that can safely receive red cells from it (standard transfusion table)
EXPECTED = {
    'O-': {'O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'},
    'O+': {'O+', 'A+', 'B+', 'AB+'},
    'A-': {'A-', 'A+', 'AB-', 'AB+'},
    'A+': {'A+', 'AB+'},
    'B-': {'B-', 'B+', 'AB-', 'AB+'},
    'B+': {'B+', 'AB+'},
    'AB-': {'AB-', 'AB+'},
    'AB+': {'AB+'},
}


class CompatibilityTests(TestCase):
    def test_full_matrix_matches_the_standard_table(self):
        for donor, recipients in EXPECTED.items():
            for recipient in EXPECTED:
                with self.subTest(donor=donor, recipient=recipient):
                    self.assertEqual(can_donate(donor, recipient), recipient in recipients)

    def test_everyone_can_donate_to_themselves(self):
        for name in EXPECTED:
            self.assertTrue(can_donate(name, name))

    def test_universal_donor_and_recipient(self):
        self.assertEqual(sum(can_donate('O-', r) for r in EXPECTED), 8)
        self.assertEqual(sum(can_donate(d, 'AB+') for d in EXPECTED), 8)

    def test_rh_positive_never_gives_to_rh_negative(self):
        for donor in EXPECTED:
            for recipient in EXPECTED:
                if donor.endswith('+') and recipient.endswith('-'):
                    self.assertFalse(can_donate(donor, recipient))

    def test_group_lookups(self):
        a_pos = BloodGroup.objects.get(name='A+')
        self.assertEqual({g.name for g in donor_groups_for(a_pos)}, {'A+', 'A-', 'O+', 'O-'})
        self.assertEqual({g.name for g in recipient_groups_for(a_pos)}, {'A+', 'AB+'})
        ab_neg = BloodGroup.objects.get(name='AB-')
        self.assertEqual({g.name for g in donor_groups_for(ab_neg)}, {'AB-', 'A-', 'B-', 'O-'})
