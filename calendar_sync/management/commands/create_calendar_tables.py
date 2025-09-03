from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Manually create calendar sync tables'

    def handle(self, *args, **options):
        
        # SQL to create the tables manually
        sql_commands = [
            """
            CREATE TABLE `calendar_sync_googlecalendarsettings` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `sync_enabled` bool NOT NULL,
                `calendar_id` varchar(255) NOT NULL,
                `last_sync` datetime(6) NULL,
                `created_at` datetime(6) NOT NULL,
                `updated_at` datetime(6) NOT NULL,
                `user_id` int NOT NULL,
                UNIQUE (`user_id`),
                CONSTRAINT `calendar_sync_googlec_user_id_f8e8c8c4_fk_auth_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
            );
            """,
            """
            CREATE TABLE `calendar_sync_googlecalendartoken` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `access_token` longtext NOT NULL,
                `refresh_token` longtext NOT NULL,
                `token_expires_at` datetime(6) NOT NULL,
                `scope` longtext NOT NULL,
                `created_at` datetime(6) NOT NULL,
                `updated_at` datetime(6) NOT NULL,
                `user_id` int NOT NULL,
                UNIQUE (`user_id`),
                CONSTRAINT `calendar_sync_googlec_user_id_4b2b4a3e_fk_auth_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
            );
            """,
            """
            CREATE TABLE `calendar_sync_taskcalendarsync` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `google_event_id` varchar(255) NOT NULL,
                `calendar_id` varchar(255) NOT NULL,
                `last_synced` datetime(6) NOT NULL,
                `sync_status` varchar(20) NOT NULL,
                `error_message` longtext NULL,
                `task_id` bigint NOT NULL,
                UNIQUE (`task_id`),
                CONSTRAINT `calendar_sync_taskca_task_id_9f8e3a9b_fk_tasks_tas` FOREIGN KEY (`task_id`) REFERENCES `tasks_task` (`id`)
            );
            """
        ]
        
        try:
            with connection.cursor() as cursor:
                for i, sql in enumerate(sql_commands, 1):
                    self.stdout.write(f"Creating table {i}/3...")
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f"✅ Table {i} created successfully"))
            
            self.stdout.write(self.style.SUCCESS('🎉 All calendar sync tables created successfully!'))
            
            # Verify tables exist
            with connection.cursor() as cursor:
                tables = [
                    'calendar_sync_googlecalendarsettings',
                    'calendar_sync_googlecalendartoken', 
                    'calendar_sync_taskcalendarsync'
                ]
                
                for table in tables:
                    cursor.execute(f"SHOW TABLES LIKE '{table}'")
                    result = cursor.fetchall()
                    if result:
                        self.stdout.write(self.style.SUCCESS(f"✅ {table} verified"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ {table} not found"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating tables: {e}'))
