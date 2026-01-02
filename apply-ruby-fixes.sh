#!/bin/bash
# Apply Ruby on Rails fixes by copying corrected files
# Run with: sudo bash apply-ruby-fixes.sh

set -e

echo "🔧 Applying Ruby on Rails database schema fixes..."
echo ""

RAILS_DIR="frameworks/ruby-rails"
FIXED_DIR="frameworks/ruby-rails-fixed"

# Copy fixed model files
echo "📝 Copying fixed model files..."
cp "$FIXED_DIR/app/models/user.rb" "$RAILS_DIR/app/models/user.rb"
cp "$FIXED_DIR/app/models/post.rb" "$RAILS_DIR/app/models/post.rb"
cp "$FIXED_DIR/app/models/comment.rb" "$RAILS_DIR/app/models/comment.rb"
echo "✅ Models updated"

# Copy fixed controller files
echo "📝 Copying fixed controller files..."
cp "$FIXED_DIR/app/controllers/users_controller.rb" "$RAILS_DIR/app/controllers/users_controller.rb"
cp "$FIXED_DIR/app/controllers/posts_controller.rb" "$RAILS_DIR/app/controllers/posts_controller.rb"
echo "✅ Controllers updated"

# Copy fixed GraphQL type files
echo "📝 Copying fixed GraphQL type files..."
cp "$FIXED_DIR/app/graphql/types/user_type.rb" "$RAILS_DIR/app/graphql/types/user_type.rb"
cp "$FIXED_DIR/app/graphql/types/post_type.rb" "$RAILS_DIR/app/graphql/types/post_type.rb"
cp "$FIXED_DIR/app/graphql/types/comment_type.rb" "$RAILS_DIR/app/graphql/types/comment_type.rb"
echo "✅ GraphQL types updated"

echo ""
echo "✅ All fixes applied successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Test the changes in Rails console:"
echo "   cd $RAILS_DIR && bundle exec rails console"
echo "   > User.first.posts"
echo "   > Post.first.author"
echo "   > Comment.first.post"
echo ""
echo "2. Optionally change ownership back to lionel:"
echo "   sudo chown -R lionel:lionel $RAILS_DIR"
echo ""
