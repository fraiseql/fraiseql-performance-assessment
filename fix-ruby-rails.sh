#!/bin/bash
# Fix Ruby on Rails database schema mappings
# Run with: sudo bash fix-ruby-rails.sh

set -e

RAILS_DIR="frameworks/ruby-rails"

echo "🔧 Fixing Ruby on Rails database schema mappings..."
echo ""

# Change ownership first
echo "📝 Step 1: Changing file ownership..."
chown -R lionel:lionel "$RAILS_DIR"
echo "✅ Ownership changed"
echo ""

# Fix model files
echo "📝 Step 2: Fixing model files..."

# User model
cat > "$RAILS_DIR/app/models/user.rb" << 'EOF'
class User < ApplicationRecord
  self.table_name = 'benchmark.tb_user'
  self.primary_key = 'pk_user'

  has_many :posts, class_name: 'Post', foreign_key: 'fk_author', dependent: :destroy
  has_many :comments, class_name: 'Comment', foreign_key: 'fk_author', dependent: :destroy
end
EOF
echo "✅ Fixed app/models/user.rb"

# Post model
cat > "$RAILS_DIR/app/models/post.rb" << 'EOF'
class Post < ApplicationRecord
  self.table_name = 'benchmark.tb_post'
  self.primary_key = 'pk_post'

  belongs_to :author, class_name: 'User', foreign_key: 'fk_author'
  has_many :comments, class_name: 'Comment', foreign_key: 'fk_post', dependent: :destroy
end
EOF
echo "✅ Fixed app/models/post.rb"

# Comment model
cat > "$RAILS_DIR/app/models/comment.rb" << 'EOF'
class Comment < ApplicationRecord
  self.table_name = 'benchmark.tb_comment'
  self.primary_key = 'pk_comment'

  belongs_to :author, class_name: 'User', foreign_key: 'fk_author'
  belongs_to :post, class_name: 'Post', foreign_key: 'fk_post'
end
EOF
echo "✅ Fixed app/models/comment.rb"

echo ""
echo "📝 Step 3: Fixing controller files..."

# Users controller
cat > "$RAILS_DIR/app/controllers/users_controller.rb" << 'EOF'
class UsersController < ApplicationController
  def show
    user = User.find_by(id: params[:id])

    if user.nil?
      render json: { error: 'User not found' }, status: :not_found
      return
    end

    render json: {
      id: user.id,
      username: user.username,
      fullName: user.full_name,
      bio: user.bio
    }
  end

  def index
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    users = User.order(:username).offset(page * size).limit(size)

    result = users.map do |user|
      {
        id: user.id,
        username: user.username,
        fullName: user.full_name,
        bio: user.bio
      }
    end

    render json: result
  end
end
EOF
echo "✅ Fixed app/controllers/users_controller.rb"

# Posts controller
cat > "$RAILS_DIR/app/controllers/posts_controller.rb" << 'EOF'
class PostsController < ApplicationController
  def show
    post = Post.includes(:author).find_by(id: params[:id])

    if post.nil?
      render json: { error: 'Post not found' }, status: :not_found
      return
    end

    render json: {
      id: post.id,
      title: post.title,
      content: post.content,
      authorId: post.author.id,  # Use author.id instead of fk_author
      createdAt: post.created_at.iso8601
    }
  end

  def index
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    posts = Post.includes(:author)
                .order(created_at: :desc)
                .offset(page * size)
                .limit(size)

    result = posts.map do |post|
      {
        id: post.id,
        title: post.title,
        content: post.content,
        authorId: post.author.id,  # Use author.id instead of fk_author
        createdAt: post.created_at.iso8601
      }
    end

    render json: result
  end

  def by_author
    author_id = params[:authorId]
    page = params.fetch(:page, 0).to_i
    size = params.fetch(:size, 10).to_i

    # Find author by UUID id, get pk_user for query
    author = User.find_by(id: author_id)
    return render json: [], status: :ok if author.nil?

    posts = Post.where(fk_author: author.pk_user)
                .includes(:author)
                .order(created_at: :desc)
                .offset(page * size)
                .limit(size)

    result = posts.map do |post|
      {
        id: post.id,
        title: post.title,
        content: post.content,
        authorId: post.author.id,
        createdAt: post.created_at.iso8601
      }
    end

    render json: result
  end
end
EOF
echo "✅ Fixed app/controllers/posts_controller.rb"

echo ""
echo "📝 Step 4: Fixing GraphQL type files..."

# User type
cat > "$RAILS_DIR/app/graphql/types/user_type.rb" << 'EOF'
module Types
  class UserType < Types::BaseObject
    field :id, ID, null: false
    field :username, String, null: false
    field :full_name, String, null: true
    field :bio, String, null: true

    field :posts, [Types::PostType], null: false
    field :comments, [Types::CommentType], null: false

    def posts
      # Use object.pk_user to query fk_author
      Post.where(fk_author: object.pk_user)
    end

    def comments
      # Use object.pk_user to query fk_author
      Comment.where(fk_author: object.pk_user)
    end
  end
end
EOF
echo "✅ Fixed app/graphql/types/user_type.rb"

# Post type
cat > "$RAILS_DIR/app/graphql/types/post_type.rb" << 'EOF'
module Types
  class PostType < Types::BaseObject
    field :id, ID, null: false
    field :title, String, null: false
    field :content, String, null: true
    field :created_at, GraphQL::Types::ISO8601DateTime, null: false

    field :author, Types::UserType, null: false
    field :comments, [Types::CommentType], null: false

    def author
      # Load author using fk_author -> pk_user
      User.find_by(pk_user: object.fk_author)
    end

    def comments
      # Use object.pk_post to query fk_post
      Comment.where(fk_post: object.pk_post)
    end
  end
end
EOF
echo "✅ Fixed app/graphql/types/post_type.rb"

# Comment type
cat > "$RAILS_DIR/app/graphql/types/comment_type.rb" << 'EOF'
module Types
  class CommentType < Types::BaseObject
    field :id, ID, null: false
    field :content, String, null: false
    field :created_at, GraphQL::Types::ISO8601DateTime, null: false

    field :author, Types::UserType, null: false
    field :post, Types::PostType, null: false

    def author
      # Load author using fk_author -> pk_user
      User.find_by(pk_user: object.fk_author)
    end

    def post
      # Load post using fk_post -> pk_post
      Post.find_by(pk_post: object.fk_post)
    end
  end
end
EOF
echo "✅ Fixed app/graphql/types/comment_type.rb"

echo ""
echo "✅ All fixes applied successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Test the changes in Rails console:"
echo "   cd $RAILS_DIR && bundle exec rails console"
echo "   User.first.posts"
echo "   Post.first.author"
echo "   Comment.first.post"
echo ""
echo "2. Consider adding DataLoaders to prevent N+1 queries"
echo "   See PHASE_1_4_RUBY_RAILS_FIX.md for DataLoader implementation"
echo ""
