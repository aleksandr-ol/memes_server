#!c:\python36\python
import pymysql
import vk_api
import json
import httplib2
import os
import settings


def captcha_handler(captcha):
    key = input("Enter captcha code {}: ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)


def vk_login():
    vk_session = vk_api.VkApi(settings.vk_uesrname, settings.vk_password, captcha_handler=captcha_handler, scope=settings.vk_scope)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    return vk_session


def get_posts(api):  # отримання постів у форматі json
    posts = api.wall.get(owner_id="-45745333", offset=1, count=100, filter="owner")
    with open('posts.json', 'w', encoding='utf-8') as file:
        json.dump(posts, file, indent=2, ensure_ascii=False)


def download_photo(url, path):
    h = httplib2.Http('.cache')
    response, content = h.request(url)
    out = open(path, 'wb')
    out.write(content)
    out.close()


# із json-відповіді Вк підготовлюємо масив для подальшого його запису в БД
# також завантажуємо фотографії в каталог групи
def process_posts_data(posts, group_dir):
    posts_data = []
    i = 0
    for post in posts['items']:
        if 'copy_history' not in post:
            posts_data.append({'owner_id': abs(int(post['owner_id'])),
                               'post_id': str(abs(int(post['owner_id']))) + '_' + str(post['id']),
                               'date': int(post['date']),
                               'text': post['text'],
                               'likes': int(post['likes']['count']),
                               'reposts': int(post['reposts']['count']),
                               'attachments': ""
                               }
                              )
            attachments = []
            if 'attachments' in post:
                for attachment in post['attachments']:
                    if attachment['type'] == 'photo':
                        photo_path = os.path.join(group_dir,
                                        str(posts_data[i]['post_id']) + '_' + str(attachment['photo']['id']) + '.jpg')
                        download_photo(url=attachment['photo']['photo_604'], path=photo_path)
                        photo_path = 'static/' + group_dir[2:] + '/' + \
                                     str(posts_data[i]['post_id']) + '_' + str(attachment['photo']['id']) + '.jpg'

                        attachments.append({'type': 'photo',
                                            'path': photo_path})

            posts_data[i]['attachments'] = json.dumps(attachments)
            i += 1
    return posts_data


# записуємо нові пости в БД
def write_into_db(posts_data):
    connection = pymysql.connect(user=settings.db_user, passwd=settings.db_pass, host=settings.db_host, port=3306, database=settings.db_name,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        for post in posts_data:
            with connection.cursor() as cursor:
                sql = "INSERT IGNORE INTO `parsed_posts`(`id`, `text`, `likes`, `reposts`, `group_id`, " \
                      "`date`, `attachments`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (post['post_id'],
                                     post['text'],
                                     post['likes'],
                                     post['reposts'],
                                     post['owner_id'],
                                     post['date'],
                                     post['attachments']))
            connection.commit()
    finally:
        connection.close()


# по переданому шляху створюємо директорію, якщо така ще не існує
def make_directory(path, name):
    full_path = os.path.join(path, name)
    if not os.path.exists(full_path):
        os.mkdir(full_path)
    return full_path


if __name__ == '__main__':
    vk_session = vk_login()

    forch_dir = make_directory(os.path.curdir, "-45745333")  # створення каталогу для форча

    get_posts(vk_session.get_api())

    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    posts_data = process_posts_data(posts, forch_dir)
    write_into_db(posts_data)
