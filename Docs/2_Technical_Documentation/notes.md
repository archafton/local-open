psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"

psql postgresql://localhost/project_tacitus_test -c "SELECT bill_number FROM bills"

psql postgresql://localhost/project_tacitus_test -c "SELECT bill_number, summary, tags, latest_action, latest_action_date, bill_text_link, bill_law_link FROM bills"

psql postgresql://localhost/project_tacitus_test -c "SELECT * FROM information_schema.columns where table_name = 'bills' order by ordinal_position;"

psql postgresql://localhost/project_tacitus_test -c "SELECT chamber,full_name,party,leadership_role,state,district,total_votes,missed_votes,total_present FROM members where current_member="true";"

psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM members;"

curl -X 'GET' 'https://api.open.fec.gov/v1/candidates/?page=1&per_page=100&is_active_candidate=true&sort=name&sort_hide_null=false&sort_null_only=false&sort_nulls_last=false&api_key=SmOPUAiaW0868JylQkn5i9hsFljgfeOiuRc1qNjf' -H 'accept: application/json' > testout.json