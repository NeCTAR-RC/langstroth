#!/bin/bash

cd ~
rm -Rf ncr002-langstroth
git clone git@code.vpac.org:ncr002-dataanalysis/ncr002-langstroth.git 
cd ncr002-langstroth/
#git status
git review -s
git remote add nectar https://github.com/NeCTAR-RC/langstroth.git
git fetch nectar
git checkout -b nectar-master nectar/master
git merge --squash master
#git status
#git add .
#git status
git commit -a
#git status
git-review