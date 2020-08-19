
from ihome import create_app, db
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager


# 创建flask的应用对象
app = create_app("develop")
# 创建flask程序的脚本管理对象
manager = Manager(app)
# 添加数据库迁移类的一个实例（第一个参数为app，第二个参数为数据库）
Migrate(app, db)
# 给app管理添加“db”的命令，用于操作数据库迁移
manager.add_command("db", MigrateCommand)



if __name__ == "__main__":
    manager.run()

