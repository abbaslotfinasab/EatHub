import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_order_inventory_permission"),
        ("inventory", "0013_reservation_status_constraint"),
        ("products", "0020_clear_unverified_order_settlement_flags"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderItemRecipeSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipe_updated_at", models.DateTimeField()),
                ("output_quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("output_unit", models.CharField(choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk")], max_length=2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_recipe_snapshots", to="accounts.business")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recipe_snapshots", to="products.order")),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_recipe_snapshot", to="products.orderitem")),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_snapshots", to="inventory.recipe")),
                ("recipe_output_ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_output_snapshots", to="inventory.ingredient")),
            ],
            options={"db_table": "order_item_recipe_snapshot"},
        ),
        migrations.AddConstraint(
            model_name="orderitemrecipesnapshot",
            constraint=models.CheckConstraint(condition=models.Q(output_quantity__gt=0), name="order_recipe_snapshot_yield_ck"),
        ),
        migrations.AddConstraint(
            model_name="orderitemrecipesnapshot",
            constraint=models.CheckConstraint(condition=models.Q(output_unit="pc"), name="order_recipe_snapshot_unit_ck"),
        ),
        migrations.AddIndex(
            model_name="orderitemrecipesnapshot",
            index=models.Index(fields=("business", "order"), name="order_snapshot_scope_ix"),
        ),
        migrations.CreateModel(
            name="OrderItemIngredientRequirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipe_input_id", models.PositiveBigIntegerField()),
                ("standard_quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("unit", models.CharField(choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk")], max_length=2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_requirements", to="inventory.ingredient")),
                ("snapshot", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requirements", to="products.orderitemrecipesnapshot")),
            ],
            options={"db_table": "order_item_ingredient_requirement"},
        ),
        migrations.AddConstraint(
            model_name="orderitemingredientrequirement",
            constraint=models.UniqueConstraint(fields=("snapshot", "ingredient"), name="order_req_snapshot_item_uq"),
        ),
        migrations.AddConstraint(
            model_name="orderitemingredientrequirement",
            constraint=models.CheckConstraint(condition=models.Q(standard_quantity__gt=0), name="order_req_qty_positive_ck"),
        ),
        migrations.AddConstraint(
            model_name="orderitemingredientrequirement",
            constraint=models.CheckConstraint(condition=models.Q(unit__in=("kg", "g", "l", "ml", "pc", "pk")), name="order_req_unit_ck"),
        ),
        migrations.AddConstraint(
            model_name="orderitemingredientrequirement",
            constraint=models.CheckConstraint(condition=models.Q(recipe_input_id__gt=0), name="order_req_input_id_ck"),
        ),
        migrations.CreateModel(
            name="OrderInventoryConsumption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.UUIDField()),
                ("payload_fingerprint", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_consumptions", to="accounts.user")),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_consumptions", to="accounts.business")),
                ("inventory_operation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_consumptions", to="inventory.inventoryoperation")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_consumptions", to="products.order")),
            ],
            options={"db_table": "order_inventory_consumption"},
        ),
        migrations.AddConstraint(
            model_name="orderinventoryconsumption",
            constraint=models.UniqueConstraint(fields=("business", "idempotency_key"), name="order_consumption_idem_uq"),
        ),
        migrations.CreateModel(
            name="OrderInventoryConsumptionLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actual_quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("unit", models.CharField(choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk")], max_length=2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("consumption", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="products.orderinventoryconsumption")),
                ("inventory_movement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_consumption_lines", to="inventory.inventoryv1stockmovement")),
                ("requirement", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consumption_lines", to="products.orderitemingredientrequirement")),
            ],
            options={"db_table": "order_inventory_consumption_line"},
        ),
        migrations.AddConstraint(
            model_name="orderinventoryconsumptionline",
            constraint=models.UniqueConstraint(fields=("consumption", "requirement"), name="order_consumption_req_uq"),
        ),
        migrations.AddConstraint(
            model_name="orderinventoryconsumptionline",
            constraint=models.CheckConstraint(condition=models.Q(actual_quantity__gte=0), name="order_consumption_qty_nonneg_ck"),
        ),
        migrations.AddConstraint(
            model_name="orderinventoryconsumptionline",
            constraint=models.CheckConstraint(condition=models.Q(unit__in=("kg", "g", "l", "ml", "pc", "pk")), name="order_consumption_unit_ck"),
        ),
    ]
