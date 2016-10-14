const gulp = require('gulp');
const del = require('del');
const runSequence = require('run-sequence');
const install = require('gulp-install');

gulp.task('clean', function() {
    return del(['./dist', './dist.zip']);
});

gulp.task('js', function() {
    return gulp.src('./app/*')
        .pipe(gulp.dest('dist/'));
});

gulp.task('node-mods', function() {
  return gulp.src('./package.json')
    .pipe(gulp.dest('dist/'))
    .pipe(install({production: true}));
});

gulp.task('build', function(callback) {
    return runSequence(
        ['clean'],
        ['js', 'node-mods'],
        callback
    );
});