# git/github
rm -rf .git
git init
git branch -M main
git add .
git commit -m "first commit"
gh repo create fingecwebsite --public
git remote add origin https://github.com/JXPM/fingecwebsite.git
git push --set-upstream origin main
