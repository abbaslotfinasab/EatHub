from django.db import migrations, models
from django.db.models import Count


def ensure_memberships_are_unique_per_business(apps, schema_editor):
    Membership = apps.get_model("accounts", "Membership")
    duplicates = (
        Membership.objects.using(schema_editor.connection.alias)
        .values("user_id", "business_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )
    if duplicates.exists():
        sample = duplicates.first()
        raise RuntimeError(
            "Cannot enforce one membership per user/business: duplicate rows exist "
            f"for user_id={sample['user_id']} and business_id={sample['business_id']}. "
            "Reconcile duplicate memberships before retrying this migration."
        )


def ensure_single_active_membership_per_user(apps, schema_editor):
    Membership = apps.get_model("accounts", "Membership")
    duplicates = (
        Membership.objects.using(schema_editor.connection.alias)
        .filter(is_active=True)
        .values("user_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )
    if duplicates.exists():
        sample = duplicates.first()
        raise RuntimeError(
            "Cannot reverse multi-active memberships while a user has more than one "
            f"active membership: user_id={sample['user_id']}. "
            "Deactivate all but one membership per user before retrying the rollback."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_business_inventory_enabled"),
    ]

    operations = [
        migrations.RunPython(
            ensure_memberships_are_unique_per_business,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="membership",
            name="one_active_business_per_user",
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(
                fields=("user", "business"),
                name="unique_user_business_membership",
            ),
        ),
        # Run first during rollback, before restoring the old user-wide constraint.
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=ensure_single_active_membership_per_user,
        ),
    ]
