#! /usr/bin/python

import os
import ConfigParser
import argparse
import boto.iam.connection
import urllib2

def get_group_users(users_response):
    user_list = []
    for user in users['get_group_response']['get_group_result']['users']:                
        user_list.append(user['user_name'])    
    return user_list

def build_search_words(args):
    search_words = {}
    n = 0
    while n < len(args.substitute):
        search_words[args.substitute[n]] = args.substitute[n+1]
        n = n +2
    return search_words   


def add_users(conn, args, users, group):
    for user_name in users:
        if not dest_users_dict.has_key(user_name):
            print 'Creating user: %s' % user_name
            conn.create_user(user_name, '/')
        else:
            print 'User: %s already exists' % user_name   
        if group and users.count(user_name) == 0:
            print 'Adding user %s to group %s' % (user_name, group_name)
            conn.add_user_to_group(group_name, user_name)
        else:
            print 'User %s already added to group %s' % (user_name, group_name)    
        if args.user_policies:
            policies = iam_src.get_all_user_policies(user_name)
            for policy_name in policies['list_user_policies_response']['list_user_policies_result']['policy_names']:
                policy = iam_src.get_user_policy(user_name, policy_name)
                policy_json = urllib2.unquote(policy['get_user_policy_response']['get_user_policy_result']['policy_document'])
                iam_dst.put_user_policy(user_name, policy_name, policy_json)  

    

def get_options():
    ''' command-line options '''

    usage = 'usage: %prog [options]'
    parser = argparse.ArgumentParser(description='Syncs IAM resources from one account to another.')

    parser.add_argument('-c', '--config-file',  metavar='my_config_file',  
            dest='config_file', default=os.environ['HOME'] + '/.iamsync', 
            help='config file containing source and destination access keys')
    parser.add_argument('-g', '--groups',  metavar='office_drones',  
            dest='groups', nargs='+', help='space separated list of groups')
    parser.add_argument('--group-policies', action='store_true',  
            dest='group_policies', default=False, help='copy policies with group')
    parser.add_argument('-r', '--recursive', action='store_true',  
            dest='recursive', default=False, help='recursively copy users with group')  
    parser.add_argument('-s', '--substitute',  metavar='foo bar bibam bop',  
            dest='substitute', nargs='+', help='simple find and replace for arns in' \
             'json policy in case you want to change a s3 target when copying policy')
    parser.add_argument('-u', '--users',  metavar='jdoe',  
            dest='users', nargs='+', help='space separated list of users')
    parser.add_argument('--user-policies', action='store_true',  
            dest='user_policies', default=False, help='copy policies with user')     
          

   
    args = parser.parse_args()
    return args


if __name__=="__main__":
    
    args = get_options()
        
    config = ConfigParser.ConfigParser()
    config.read(args.config_file)
    
    iam_src = boto.iam.connection.IAMConnection(aws_access_key_id=config.get('src', 'aws_access_key_id'), 
                                                aws_secret_access_key= config.get('src', 'aws_secret_access_key'))
    iam_dst = boto.iam.connection.IAMConnection(aws_access_key_id=config.get('dest', 'aws_access_key_id'), 
                                                aws_secret_access_key= config.get('dest', 'aws_secret_access_key'))
    
    
    dest_groups = iam_dst.get_all_groups('/')
    dest_users = iam_dst.get_all_users('/')
    dest_groups_dict = {}
    dest_users_dict = {}
    
    for group in dest_groups['list_groups_response']['list_groups_result']['groups']:
        dest_groups_dict[group['group_name']] = 0
    for user in dest_users['list_users_response']['list_users_result']['users']:
        dest_users_dict[user['user_name']] = 0        
    
    if args.groups:
    
        for group_name in args.groups:
            try:
                users = iam_src.get_group(group_name)
            except Exception, err:
                print Exception, err                
        if not dest_groups_dict.has_key(group_name):
            iam_dst.create_group(group_name, '/')
        else:
            print 'Group: %s already exists.' % group_name
        if args.group_policies:
            policies = iam_src.get_all_group_policies(group_name)
            for policy_name in policies['list_group_policies_response']['list_group_policies_result']['policy_names']:
                policy = iam_src.get_group_policy(group_name, policy_name)
                policy_json = urllib2.unquote(policy['get_group_policy_response']['get_group_policy_result']['policy_document'])
                if args.substitute:
                    search_words = build_search_words(args)
                    for find_string, replace_string in search_words.items():
                        policy_json = policy_json.replace(find_string, replace_string)                
                iam_dst.put_group_policy(group_name, policy_name, policy_json)        
                            
        if args.recursive:
            group_user_list = get_group_users (users['get_group_response']['get_group_result']['users'] )           
            add_users(iam_dst, args, group_user_list, group)
        
                 
    
    if args.users:
        add_users(iam_dst, args, args.users, False)





