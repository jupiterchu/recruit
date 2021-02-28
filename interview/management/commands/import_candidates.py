import csv

from django.core.management import BaseCommand

from interview.models import Candidate


# manage.py import_candidates --path file.csv
class Command(BaseCommand):
    help = "从一个 CSV 中导入数据到数据库"

    # 定义一个命令行参数，'--' 表示长命令
    def add_arguments(self, parser):
        parser.add_argument('--path', type=str)

    # 命令行处理逻辑
    def handle(self, *args, **options):
        path = options['path']
        with open(path, 'rt', encoding='GBK') as f:
            reader = csv.reader(f, dialect='excel', delimiter=';')  # 指定分割符
            for row in reader:
                # 每行第 N 个单元格
                candidate = Candidate.objects.create(
                    username=row[0],
                    city=row[1],
                    phone=row[2],
                    bachelor_school=row[3],
                    major=row[4],
                    degree=row[5],
                    test_score_of_general_ability=row[6],
                    paper_score=row[7]
                )
                print(candidate)
